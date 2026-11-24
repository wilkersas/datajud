# MCP Datajud (CNJ)

Servidor MCP (Model Context Protocol) para consultar a **API Pública do
Datajud**, do CNJ, que disponibilita metadados de processos públicos de
91 tribunais brasileiros (Tribunais Superiores, Justiça Federal, Estadual,
do Trabalho, Eleitoral e Militar).

## Ferramentas disponíveis

| Ferramenta | Uso |
|---|---|
| `listar_tribunais` | Lista/filtra os tribunais e seus aliases (ex.: `tjgo`, `trf1`, `tst`) |
| `buscar_processo_por_numero` | Busca um processo pelo número único CNJ |
| `buscar_processos` | Busca com filtros comuns: classe, órgão julgador, assunto, datas, texto livre |
| `consulta_avancada` | Envia uma query Elasticsearch (DSL) completa, para casos não cobertos pelos filtros acima |

Todas retornam um resumo com `total_encontrado`, `quantidade_retornada`,
`processos` (lista de metadados) e `proximo_search_after` (para paginar
buscas com muitos resultados, usando o parâmetro `search_after`).

## Instalação

Dependências (já presentes neste ambiente; em outra máquina, instale):

```bash
pip install -r requirements.txt
```

Requer `mcp >= 2.0` e `requests`.

## Configuração da API Key

A API Pública do Datajud usa uma **chave pública** divulgada pelo CNJ,
que pode ser alterada por eles a qualquer momento. O servidor já traz
embutida a chave atual que você forneceu, mas é recomendável poder
sobrescrevê-la sem editar código:

```bash
export DATAJUD_API_KEY="cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
```

Se a chave for alterada pelo CNJ, basta atualizar essa variável de
ambiente (a chave vigente fica sempre na Wiki oficial:
https://datajud-wiki.cnj.jus.br/api-publica/).

## Como adicionar ao Claude Desktop / Claude Code

Edite o arquivo de configuração de MCP servers (no Claude Desktop, em
`claude_desktop_config.json`) e adicione:

```json
{
  "mcpServers": {
    "datajud-cnj": {
      "command": "python3",
      "args": ["/caminho/completo/para/datajud-mcp/server.py"],
      "env": {
        "DATAJUD_API_KEY": "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
      }
    }
  }
}
```

Ajuste `/caminho/completo/para/` para onde você salvar os arquivos
(`server.py` e `tribunais.py` precisam estar na mesma pasta).

Depois de configurar, reinicie o Claude Desktop (ou recarregue os MCP
servers no Claude Code) para que as ferramentas apareçam.

## Usar no claude.ai (navegador) como conector personalizado

O claude.ai no navegador não roda programas no seu computador: ele se
conecta a servidores MCP **remotos**, por HTTPS. Por isso o servidor precisa
estar hospedado na internet. Ele já tem um modo HTTP:

```bash
MCP_TRANSPORT=http PORT=8000 MCP_PATH_SECRET=um-segredo-longo python server.py
# endpoint: http://localhost:8000/um-segredo-longo/mcp
```

`MCP_PATH_SECRET` é opcional, mas recomendado: sem ele, qualquer pessoa que
descubra a URL pode usar o seu servidor.

### Deploy gratuito no Render

1. Envie esta pasta para um repositório no GitHub.
2. Em https://render.com, crie uma conta e vá em **New → Blueprint**.
   Escolha o repositório: o `render.yaml` já configura tudo e gera
   um `MCP_PATH_SECRET` aleatório.
3. Depois do deploy, abra o serviço → **Environment** e copie o valor de
   `MCP_PATH_SECRET`. Sua URL será:
   `https://<nome-do-servico>.onrender.com/<MCP_PATH_SECRET>/mcp`

No plano gratuito do Render o serviço "dorme" após cerca de 15 min sem uso;
a primeira chamada depois disso leva cerca de 1 min a mais para acordar.

### Adicionar no claude.ai

1. **Configurações → Conectores → Adicionar conector personalizado**.
2. Nome: `Datajud CNJ`; URL: a URL acima (terminando em `/mcp`).
   Deixe os campos de OAuth em branco.
3. Em uma conversa, ative o conector no botão de ferramentas e peça, por
   exemplo: "Busque o processo 0000832-34.2018.4.05.8300 no TRF5".

## Exemplos de uso (depois de conectado)

- "Liste os tribunais de Goiás" → `listar_tribunais(busca="goiás")`
- "Busque o processo 0000832-34.2018.4.05.8300 no TJGO" →
  `buscar_processo_por_numero(tribunal="tjgo", numero_processo="0000832-34.2018.4.05.8300")`
- "Busque processos da 10ª Câmara Cível do TJGO ajuizados em 2024" →
  `buscar_processos(tribunal="tjgo", orgao_julgador_nome="10ª Câmara Cível", data_ajuizamento_inicio="2024-01-01", data_ajuizamento_fim="2024-12-31")`

## Observações importantes

- A API do Datajud é baseada em **Elasticsearch**: os nomes de campos
  (`numeroProcesso`, `classe.codigo`, `orgaoJulgador.nome`,
  `assuntos.codigo`, `dataAjuizamento`, etc.) seguem o mapeamento de
  metadados processuais do CNJ (Resolução nº 331/2020 e a estrutura de
  dados do Datajud). Se um filtro não retornar o esperado, use
  `consulta_avancada` para inspecionar/ajustar a query diretamente.
- Por padrão, resultados são paginados em blocos de até 100 (ajustável
  via `tamanho`). Para navegar além do limite padrão do Elasticsearch
  (10.000 resultados via `from`/`size`), use o valor retornado em
  `proximo_search_after` como `search_after` na chamada seguinte.
- **Instabilidade do Datajud:** a API do CNJ fica sobrecarregada com
  frequência e responde `429` (`es_rejected_execution_exception`) ou `200`
  com parte dos shards falhando. O servidor tenta de novo automaticamente
  com backoff exponencial e, quando a resposta vem parcial, inclui o campo
  `aviso` ("Resultado possivelmente INCOMPLETO"). Nesse caso, repita a
  consulta. Uma busca pode levar de 30 s a 2-3 min nesses momentos.
- Variáveis opcionais: `DATAJUD_TIMEOUT` (segundos por tentativa, padrão
  90) e `DATAJUD_MAX_TENTATIVAS` (padrão 4).
- Testado contra a API real em 23/11/2026: autenticação com a chave
  pública OK, `buscar_processo_por_numero`, `buscar_processos` (órgão
  julgador e texto livre) e `consulta_avancada` retornaram dados, todos
  com aviso de shards parciais por sobrecarga do CNJ.
