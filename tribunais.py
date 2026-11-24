"""
Mapeamento de tribunais/aliases da API Pública do Datajud (CNJ).

Cada entrada mapeia um "alias" (usado nas ferramentas do MCP) para:
  - nome: nome completo do tribunal
  - grupo: agrupamento (Tribunais Superiores, Justiça Federal, etc.)
  - endpoint: alias técnico usado na URL da API (ex.: "tjgo" -> api_publica_tjgo)

A URL final de consulta é sempre:
    https://api-publica.datajud.cnj.jus.br/api_publica_{endpoint}/_search
"""

from typing import Optional

BASE_URL = "https://api-publica.datajud.cnj.jus.br"

# (alias_amigavel, nome_completo, grupo, endpoint_tecnico)
_TRIBUNAIS_RAW = [
    # Tribunais Superiores
    ("tst", "Tribunal Superior do Trabalho", "Tribunais Superiores", "tst"),
    ("tse", "Tribunal Superior Eleitoral", "Tribunais Superiores", "tse"),
    ("stj", "Superior Tribunal de Justiça", "Tribunais Superiores", "stj"),
    ("stm", "Superior Tribunal Militar", "Tribunais Superiores", "stm"),

    # Justiça Federal
    ("trf1", "Tribunal Regional Federal da 1ª Região", "Justiça Federal", "trf1"),
    ("trf2", "Tribunal Regional Federal da 2ª Região", "Justiça Federal", "trf2"),
    ("trf3", "Tribunal Regional Federal da 3ª Região", "Justiça Federal", "trf3"),
    ("trf4", "Tribunal Regional Federal da 4ª Região", "Justiça Federal", "trf4"),
    ("trf5", "Tribunal Regional Federal da 5ª Região", "Justiça Federal", "trf5"),
    ("trf6", "Tribunal Regional Federal da 6ª Região", "Justiça Federal", "trf6"),

    # Justiça Estadual
    ("tjac", "Tribunal de Justiça do Acre", "Justiça Estadual", "tjac"),
    ("tjal", "Tribunal de Justiça de Alagoas", "Justiça Estadual", "tjal"),
    ("tjam", "Tribunal de Justiça do Amazonas", "Justiça Estadual", "tjam"),
    ("tjap", "Tribunal de Justiça do Amapá", "Justiça Estadual", "tjap"),
    ("tjba", "Tribunal de Justiça da Bahia", "Justiça Estadual", "tjba"),
    ("tjce", "Tribunal de Justiça do Ceará", "Justiça Estadual", "tjce"),
    ("tjdft", "TJ do Distrito Federal e Territórios", "Justiça Estadual", "tjdft"),
    ("tjes", "Tribunal de Justiça do Espírito Santo", "Justiça Estadual", "tjes"),
    ("tjgo", "Tribunal de Justiça do Goiás", "Justiça Estadual", "tjgo"),
    ("tjma", "Tribunal de Justiça do Maranhão", "Justiça Estadual", "tjma"),
    ("tjmg", "Tribunal de Justiça de Minas Gerais", "Justiça Estadual", "tjmg"),
    ("tjms", "TJ do Mato Grosso do Sul", "Justiça Estadual", "tjms"),
    ("tjmt", "Tribunal de Justiça do Mato Grosso", "Justiça Estadual", "tjmt"),
    ("tjpa", "Tribunal de Justiça do Pará", "Justiça Estadual", "tjpa"),
    ("tjpb", "Tribunal de Justiça da Paraíba", "Justiça Estadual", "tjpb"),
    ("tjpe", "Tribunal de Justiça de Pernambuco", "Justiça Estadual", "tjpe"),
    ("tjpi", "Tribunal de Justiça do Piauí", "Justiça Estadual", "tjpi"),
    ("tjpr", "Tribunal de Justiça do Paraná", "Justiça Estadual", "tjpr"),
    ("tjrj", "Tribunal de Justiça do Rio de Janeiro", "Justiça Estadual", "tjrj"),
    ("tjrn", "TJ do Rio Grande do Norte", "Justiça Estadual", "tjrn"),
    ("tjro", "Tribunal de Justiça de Rondônia", "Justiça Estadual", "tjro"),
    ("tjrr", "Tribunal de Justiça de Roraima", "Justiça Estadual", "tjrr"),
    ("tjrs", "Tribunal de Justiça do Rio Grande do Sul", "Justiça Estadual", "tjrs"),
    ("tjsc", "Tribunal de Justiça de Santa Catarina", "Justiça Estadual", "tjsc"),
    ("tjse", "Tribunal de Justiça de Sergipe", "Justiça Estadual", "tjse"),
    ("tjsp", "Tribunal de Justiça de São Paulo", "Justiça Estadual", "tjsp"),
    ("tjto", "Tribunal de Justiça do Tocantins", "Justiça Estadual", "tjto"),

    # Justiça do Trabalho
    ("trt1", "Tribunal Regional do Trabalho da 1ª Região", "Justiça do Trabalho", "trt1"),
    ("trt2", "Tribunal Regional do Trabalho da 2ª Região", "Justiça do Trabalho", "trt2"),
    ("trt3", "Tribunal Regional do Trabalho da 3ª Região", "Justiça do Trabalho", "trt3"),
    ("trt4", "Tribunal Regional do Trabalho da 4ª Região", "Justiça do Trabalho", "trt4"),
    ("trt5", "Tribunal Regional do Trabalho da 5ª Região", "Justiça do Trabalho", "trt5"),
    ("trt6", "Tribunal Regional do Trabalho da 6ª Região", "Justiça do Trabalho", "trt6"),
    ("trt7", "Tribunal Regional do Trabalho da 7ª Região", "Justiça do Trabalho", "trt7"),
    ("trt8", "Tribunal Regional do Trabalho da 8ª Região", "Justiça do Trabalho", "trt8"),
    ("trt9", "Tribunal Regional do Trabalho da 9ª Região", "Justiça do Trabalho", "trt9"),
    ("trt10", "Tribunal Regional do Trabalho da 10ª Região", "Justiça do Trabalho", "trt10"),
    ("trt11", "Tribunal Regional do Trabalho da 11ª Região", "Justiça do Trabalho", "trt11"),
    ("trt12", "Tribunal Regional do Trabalho da 12ª Região", "Justiça do Trabalho", "trt12"),
    ("trt13", "Tribunal Regional do Trabalho da 13ª Região", "Justiça do Trabalho", "trt13"),
    ("trt14", "Tribunal Regional do Trabalho da 14ª Região", "Justiça do Trabalho", "trt14"),
    ("trt15", "Tribunal Regional do Trabalho da 15ª Região", "Justiça do Trabalho", "trt15"),
    ("trt16", "Tribunal Regional do Trabalho da 16ª Região", "Justiça do Trabalho", "trt16"),
    ("trt17", "Tribunal Regional do Trabalho da 17ª Região", "Justiça do Trabalho", "trt17"),
    ("trt18", "Tribunal Regional do Trabalho da 18ª Região", "Justiça do Trabalho", "trt18"),
    ("trt19", "Tribunal Regional do Trabalho da 19ª Região", "Justiça do Trabalho", "trt19"),
    ("trt20", "Tribunal Regional do Trabalho da 20ª Região", "Justiça do Trabalho", "trt20"),
    ("trt21", "Tribunal Regional do Trabalho da 21ª Região", "Justiça do Trabalho", "trt21"),
    ("trt22", "Tribunal Regional do Trabalho da 22ª Região", "Justiça do Trabalho", "trt22"),
    ("trt23", "Tribunal Regional do Trabalho da 23ª Região", "Justiça do Trabalho", "trt23"),
    ("trt24", "Tribunal Regional do Trabalho da 24ª Região", "Justiça do Trabalho", "trt24"),

    # Justiça Eleitoral
    ("tre-ac", "Tribunal Regional Eleitoral do Acre", "Justiça Eleitoral", "tre-ac"),
    ("tre-al", "Tribunal Regional Eleitoral de Alagoas", "Justiça Eleitoral", "tre-al"),
    ("tre-am", "Tribunal Regional Eleitoral do Amazonas", "Justiça Eleitoral", "tre-am"),
    ("tre-ap", "Tribunal Regional Eleitoral do Amapá", "Justiça Eleitoral", "tre-ap"),
    ("tre-ba", "Tribunal Regional Eleitoral da Bahia", "Justiça Eleitoral", "tre-ba"),
    ("tre-ce", "Tribunal Regional Eleitoral do Ceará", "Justiça Eleitoral", "tre-ce"),
    ("tre-dft", "Tribunal Regional Eleitoral do Distrito Federal", "Justiça Eleitoral", "tre-dft"),
    ("tre-es", "Tribunal Regional Eleitoral do Espírito Santo", "Justiça Eleitoral", "tre-es"),
    ("tre-go", "Tribunal Regional Eleitoral do Goiás", "Justiça Eleitoral", "tre-go"),
    ("tre-ma", "Tribunal Regional Eleitoral do Maranhão", "Justiça Eleitoral", "tre-ma"),
    ("tre-mg", "Tribunal Regional Eleitoral de Minas Gerais", "Justiça Eleitoral", "tre-mg"),
    ("tre-ms", "Tribunal Regional Eleitoral do Mato Grosso do Sul", "Justiça Eleitoral", "tre-ms"),
    ("tre-mt", "Tribunal Regional Eleitoral do Mato Grosso", "Justiça Eleitoral", "tre-mt"),
    ("tre-pa", "Tribunal Regional Eleitoral do Pará", "Justiça Eleitoral", "tre-pa"),
    ("tre-pb", "Tribunal Regional Eleitoral da Paraíba", "Justiça Eleitoral", "tre-pb"),
    ("tre-pe", "Tribunal Regional Eleitoral de Pernambuco", "Justiça Eleitoral", "tre-pe"),
    ("tre-pi", "Tribunal Regional Eleitoral do Piauí", "Justiça Eleitoral", "tre-pi"),
    ("tre-pr", "Tribunal Regional Eleitoral do Paraná", "Justiça Eleitoral", "tre-pr"),
    ("tre-rj", "Tribunal Regional Eleitoral do Rio de Janeiro", "Justiça Eleitoral", "tre-rj"),
    ("tre-rn", "Tribunal Regional Eleitoral do Rio Grande do Norte", "Justiça Eleitoral", "tre-rn"),
    ("tre-ro", "Tribunal Regional Eleitoral de Rondônia", "Justiça Eleitoral", "tre-ro"),
    ("tre-rr", "Tribunal Regional Eleitoral de Roraima", "Justiça Eleitoral", "tre-rr"),
    ("tre-rs", "Tribunal Regional Eleitoral do Rio Grande do Sul", "Justiça Eleitoral", "tre-rs"),
    ("tre-sc", "Tribunal Regional Eleitoral de Santa Catarina", "Justiça Eleitoral", "tre-sc"),
    ("tre-se", "Tribunal Regional Eleitoral de Sergipe", "Justiça Eleitoral", "tre-se"),
    ("tre-sp", "Tribunal Regional Eleitoral de São Paulo", "Justiça Eleitoral", "tre-sp"),
    ("tre-to", "Tribunal Regional Eleitoral do Tocantins", "Justiça Eleitoral", "tre-to"),

    # Justiça Militar
    ("tjmmg", "Tribunal de Justiça Militar de Minas Gerais", "Justiça Militar", "tjmmg"),
    ("tjmrs", "Tribunal de Justiça Militar do Rio Grande do Sul", "Justiça Militar", "tjmrs"),
    ("tjmsp", "Tribunal de Justiça Militar de São Paulo", "Justiça Militar", "tjmsp"),
]

TRIBUNAIS = {
    alias: {"nome": nome, "grupo": grupo, "endpoint": endpoint}
    for alias, nome, grupo, endpoint in _TRIBUNAIS_RAW
}


def get_search_url(alias: str) -> str:
    """Retorna a URL completa de busca (_search) para o alias do tribunal."""
    alias = alias.strip().lower()
    if alias not in TRIBUNAIS:
        disponiveis = ", ".join(sorted(TRIBUNAIS.keys()))
        raise ValueError(
            f"Alias de tribunal '{alias}' não reconhecido. "
            f"Use listar_tribunais para ver as opções. Aliases disponíveis: {disponiveis}"
        )
    endpoint = TRIBUNAIS[alias]["endpoint"]
    return f"{BASE_URL}/api_publica_{endpoint}/_search"


def buscar_tribunais(termo: Optional[str] = None):
    """Busca tribunais por termo (nome ou alias), case-insensitive. Sem termo, retorna todos."""
    if not termo:
        itens = TRIBUNAIS.items()
    else:
        termo_lower = termo.strip().lower()
        itens = [
            (alias, info)
            for alias, info in TRIBUNAIS.items()
            if termo_lower in alias.lower() or termo_lower in info["nome"].lower()
        ]
    return [
        {"alias": alias, "nome": info["nome"], "grupo": info["grupo"]}
        for alias, info in itens
    ]
