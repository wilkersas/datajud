#!/usr/bin/env python3
"""
Servidor MCP para a API Pública do Datajud (CNJ).

Expõe ferramentas para consultar metadados de processos públicos dos
tribunais brasileiros através da API Pública do Datajud, mantida pelo
CNJ (Conselho Nacional de Justiça), via protocolo Elasticsearch (_search).

Documentação oficial: https://datajud-wiki.cnj.jus.br/api-publica/

Configuração:
    A API Key pode ser definida via variável de ambiente DATAJUD_API_KEY.
    Caso não seja definida, usa-se a chave pública padrão divulgada na Wiki
    do CNJ (sujeita a alteração pelo próprio CNJ a qualquer momento).
"""

import json
import os
import sys
import time
from typing import Any, Optional

import requests

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from tribunais import buscar_tribunais, get_search_url

# Chave pública padrão divulgada na Wiki do Datajud/CNJ.
# Pode ser sobrescrita pela variável de ambiente DATAJUD_API_KEY, já que o
# CNJ pode alterá-la a qualquer momento por razões de segurança.
DEFAULT_API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="

TIMEOUT_SEGUNDOS = int(os.environ.get("DATAJUD_TIMEOUT", "60"))
# Prazo total (todas as tentativas somadas) para não travar o chat.
PRAZO_TOTAL_SEGUNDOS = int(os.environ.get("DATAJUD_PRAZO_TOTAL", "120"))
# A API do Datajud frequentemente fica sobrecarregada e devolve 429
# (es_rejected_execution_exception) ou 5xx; tentamos novamente com backoff.
MAX_TENTATIVAS = int(os.environ.get("DATAJUD_MAX_TENTATIVAS", "4"))
STATUS_RETENTAVEIS = {429, 502, 503, 504}

mcp = MCPServer(
    name="datajud-cnj",
    title="Datajud CNJ (API Pública)",
    instructions=(
        "Ferramentas para consultar metadados de processos públicos dos "
        "tribunais brasileiros via API Pública do Datajud/CNJ. Use "
        "listar_tribunais para descobrir o alias correto do tribunal, "
        "buscar_processo_por_numero para localizar um processo específico "
        "pelo número (CNJ), buscar_processos para pesquisas com filtros "
        "(classe, órgão julgador, datas, assunto, texto livre) e "
        "consulta_avancada para enviar uma query Elasticsearch (DSL) "
        "completa quando for necessário algo mais específico."
    ),
)


def _api_key() -> str:
    return os.environ.get("DATAJUD_API_KEY", DEFAULT_API_KEY)


def _headers() -> dict:
    return {
        "Authorization": f"APIKey {_api_key()}",
        "Content-Type": "application/json",
    }


def _executar_busca(tribunal: str, corpo: dict) -> dict:
    """Executa uma requisição POST contra o endpoint _search do tribunal informado."""
    try:
        url = get_search_url(tribunal)
    except ValueError as exc:
        raise ToolError(str(exc)) from exc
    resposta = None
    inicio = time.monotonic()
    for tentativa in range(1, MAX_TENTATIVAS + 1):
        restante = PRAZO_TOTAL_SEGUNDOS - (time.monotonic() - inicio)
        if restante < 5:
            break
        try:
            resposta = requests.post(
                url,
                headers=_headers(),
                data=json.dumps(corpo),
                timeout=min(TIMEOUT_SEGUNDOS, restante),
            )
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            if tentativa == MAX_TENTATIVAS or time.monotonic() - inicio > PRAZO_TOTAL_SEGUNDOS - 10:
                raise ToolError(
                    f"A API do Datajud não respondeu a tempo ({tentativa} tentativa(s), "
                    f"{int(time.monotonic() - inicio)} s). O servidor do CNJ costuma ficar "
                    "sobrecarregado; tente novamente em alguns minutos ou use filtros "
                    f"mais específicos. Detalhe: {exc}"
                ) from exc
            time.sleep(2 ** tentativa)
            continue
        except requests.exceptions.RequestException as exc:
            raise ToolError(f"Falha de conexão com a API do Datajud: {exc}") from exc

        if resposta.status_code in STATUS_RETENTAVEIS and tentativa < MAX_TENTATIVAS:
            time.sleep(2 ** tentativa)
            continue
        break

    if resposta is None:
        raise ToolError(
            f"A API do Datajud não respondeu dentro de {PRAZO_TOTAL_SEGUNDOS} s "
            "(sobrecarga do CNJ). Tente novamente em alguns minutos."
        )
    if resposta.status_code == 401:
        raise ToolError(
            "Autenticação recusada (401). A API Key pode estar desatualizada - "
            "o CNJ pode alterá-la a qualquer momento. Verifique a chave atual em "
            "https://datajud-wiki.cnj.jus.br/api-publica/ e configure a variável "
            "de ambiente DATAJUD_API_KEY."
        )
    if resposta.status_code == 429:
        raise ToolError(
            f"A API do Datajud recusou a busca (429) após {tentativa} tentativa(s) - "
            "normalmente é sobrecarga no Elasticsearch do CNJ. Tente novamente em instantes."
        )
    if not resposta.ok:
        raise ToolError(
            f"Erro HTTP {resposta.status_code} do Datajud: {resposta.text[:1000]}"
        )

    try:
        return resposta.json()
    except ValueError as exc:
        raise ToolError(f"Resposta inesperada (não-JSON) do Datajud: {resposta.text[:500]}") from exc


def _formatar_hits(resultado: dict) -> dict:
    """Extrai e simplifica os hits de uma resposta Elasticsearch do Datajud."""
    hits_obj = resultado.get("hits", {})
    total = hits_obj.get("total", {})
    total_valor = total.get("value") if isinstance(total, dict) else total
    hits = hits_obj.get("hits", [])

    processos = []
    ultimo_sort = None
    for hit in hits:
        fonte = hit.get("_source", {})
        processos.append(fonte)
        if "sort" in hit:
            ultimo_sort = hit["sort"]

    saida = {
        "total_encontrado": total_valor,
        "quantidade_retornada": len(processos),
        "processos": processos,
        "proximo_search_after": ultimo_sort,
    }

    # O Datajud às vezes responde 200 com parte dos shards falhando
    # (sobrecarga). Nesse caso o resultado pode estar incompleto.
    shards = resultado.get("_shards", {})
    falhos = shards.get("failed", 0)
    if falhos:
        saida["aviso"] = (
            f"Resultado possivelmente INCOMPLETO: {falhos} de {shards.get('total')} "
            "shards falharam no Datajud (sobrecarga do servidor do CNJ). "
            "Repita a consulta para confirmar."
        )
    return saida


@mcp.tool()
def listar_tribunais(busca: Optional[str] = None) -> list[dict]:
    """Lista os tribunais disponíveis na API Pública do Datajud e seus aliases.

    Use esta ferramenta primeiro para descobrir o alias correto a ser usado
    nas demais ferramentas (ex.: "tjgo" para o Tribunal de Justiça de Goiás,
    "trf1" para o TRF da 1ª Região, "tst" para o Tribunal Superior do Trabalho).

    Args:
        busca: termo opcional para filtrar por nome ou alias (ex.: "goiás",
            "trabalho", "tjgo"). Se omitido, retorna todos os tribunais.
    """
    return buscar_tribunais(busca)


@mcp.tool()
def buscar_processo_por_numero(tribunal: str, numero_processo: str) -> dict:
    """Busca um processo específico pelo número único CNJ em um tribunal.

    Args:
        tribunal: alias do tribunal (ex.: "tjgo", "trf1", "tst"). Use
            listar_tribunais para ver as opções.
        numero_processo: número do processo no padrão CNJ, com ou sem
            formatação (ex.: "00008323420184058300" ou
            "0000832-34.2018.4.05.8300").
    """
    numero_limpo = "".join(ch for ch in numero_processo if ch.isdigit())
    corpo = {"query": {"match": {"numeroProcesso": numero_limpo}}}
    resultado = _executar_busca(tribunal, corpo)
    return _formatar_hits(resultado)


@mcp.tool()
def buscar_processos(
    tribunal: str,
    classe_codigo: Optional[int] = None,
    orgao_julgador_nome: Optional[str] = None,
    assunto_codigo: Optional[int] = None,
    data_ajuizamento_inicio: Optional[str] = None,
    data_ajuizamento_fim: Optional[str] = None,
    texto_livre: Optional[str] = None,
    tamanho: int = 10,
    search_after: Optional[list] = None,
) -> dict:
    """Busca processos em um tribunal usando filtros comuns.

    Combina os filtros informados em uma query Elasticsearch (bool/must).
    Pelo menos um filtro deve ser informado além do tribunal.

    Args:
        tribunal: alias do tribunal (ex.: "tjgo"). Use listar_tribunais.
        classe_codigo: código numérico da classe processual (campo
            classe.codigo), conforme Tabelas Processuais Unificadas do CNJ.
        orgao_julgador_nome: nome (ou parte do nome) do órgão julgador
            (campo orgaoJulgador.nome), ex.: "10ª Câmara Cível".
        assunto_codigo: código numérico do assunto (campo assuntos.codigo).
        data_ajuizamento_inicio: data inicial (formato "AAAA-MM-DD") para
            filtrar por dataAjuizamento (inclusive).
        data_ajuizamento_fim: data final (formato "AAAA-MM-DD") para
            filtrar por dataAjuizamento (inclusive).
        texto_livre: termo de busca livre (usa multi_match contra os
            principais campos textuais do processo).
        tamanho: quantidade máxima de resultados a retornar (padrão 10,
            máximo recomendado 100 por página).
        search_after: valores de ordenação (campo "sort") retornados pela
            busca anterior em "proximo_search_after", para paginar além do
            limite padrão do Elasticsearch. Omita na primeira página.
    """
    must: list[dict] = []

    if classe_codigo is not None:
        must.append({"match": {"classe.codigo": classe_codigo}})
    if orgao_julgador_nome:
        must.append({"match": {"orgaoJulgador.nome": orgao_julgador_nome}})
    if assunto_codigo is not None:
        must.append({"match": {"assuntos.codigo": assunto_codigo}})
    if data_ajuizamento_inicio or data_ajuizamento_fim:
        intervalo: dict[str, str] = {}
        if data_ajuizamento_inicio:
            intervalo["gte"] = data_ajuizamento_inicio
        if data_ajuizamento_fim:
            intervalo["lte"] = data_ajuizamento_fim
        must.append({"range": {"dataAjuizamento": intervalo}})
    if texto_livre:
        must.append(
            {
                "multi_match": {
                    "query": texto_livre,
                    "fields": [
                        "classe.nome",
                        "assuntos.nome",
                        "orgaoJulgador.nome",
                        "numeroProcesso",
                    ],
                }
            }
        )

    if not must:
        raise ToolError(
            "Informe ao menos um filtro (classe_codigo, orgao_julgador_nome, "
            "assunto_codigo, datas ou texto_livre) além do tribunal."
        )

    corpo: dict[str, Any] = {
        "query": {"bool": {"must": must}},
        "size": max(1, min(tamanho, 100)),
        "sort": [{"@timestamp": {"order": "asc"}}],
    }
    if search_after:
        corpo["search_after"] = search_after

    resultado = _executar_busca(tribunal, corpo)
    return _formatar_hits(resultado)


@mcp.tool()
def consulta_avancada(tribunal: str, query_json: str, tamanho: Optional[int] = None) -> dict:
    """Executa uma consulta Elasticsearch (DSL) completa e personalizada.

    Use esta ferramenta quando os filtros de buscar_processos não forem
    suficientes e você já souber montar uma query no formato DSL do
    Elasticsearch aceito pela API do Datajud (ex.: queries aninhadas,
    agregações, múltiplos sorts, etc.).

    Args:
        tribunal: alias do tribunal (ex.: "tjgo"). Use listar_tribunais.
        query_json: corpo da requisição em formato JSON (string), seguindo
            a sintaxe de query DSL do Elasticsearch. Exemplo:
            '{"query": {"match": {"numeroProcesso": "00008323420184058300"}}}'
        tamanho: se informado, sobrescreve/define o campo "size" do corpo
            da requisição.
    """
    try:
        corpo = json.loads(query_json)
    except json.JSONDecodeError as exc:
        raise ToolError(f"query_json inválido - não é um JSON válido: {exc}") from exc

    if not isinstance(corpo, dict):
        raise ToolError("query_json deve representar um objeto JSON (dict).")

    if tamanho is not None:
        corpo["size"] = max(1, min(tamanho, 100))

    resultado = _executar_busca(tribunal, corpo)
    return _formatar_hits(resultado)


def main() -> None:
    """Inicia o servidor.

    - Sem configuração: modo stdio (Claude Desktop / Claude Code local).
    - MCP_TRANSPORT=http (ou quando a variável PORT existe, como em Render,
      Railway, Fly.io etc.): modo HTTP "streamable-http", para usar como
      conector personalizado no claude.ai (navegador).
    """
    transporte = os.environ.get("MCP_TRANSPORT", "").lower()
    if transporte in ("http", "streamable-http") or (not transporte and "PORT" in os.environ):
        from mcp.server.transport_security import TransportSecuritySettings

        # Caminho opcional com segredo, para que só quem conhece a URL use
        # o servidor: MCP_PATH_SECRET=abc123 -> https://seu-host/abc123/mcp
        segredo = os.environ.get("MCP_PATH_SECRET", "").strip("/")
        caminho = f"/{segredo}/mcp" if segredo else "/mcp"

        mcp.run(
            transport="streamable-http",
            host=os.environ.get("HOST", "0.0.0.0"),
            port=int(os.environ.get("PORT", "8000")),
            streamable_http_path=caminho,
            stateless_http=True,
            json_response=True,
            # Servidor público atrás de proxy/HTTPS do provedor: o Host
            # header será o domínio público, então desligamos a checagem
            # de DNS rebinding (pensada para servidores em localhost).
            transport_security=TransportSecuritySettings(
                enable_dns_rebinding_protection=False
            ),
        )
    else:
        mcp.run()


if __name__ == "__main__":
    main()
