"""G5 - O-rings e elementos de vedação relacionados.

Mapa validado família por família. Este módulo não consulta estoque, UI,
Supabase ou orçamento.

Observações:
- componentes explicitamente ausentes ficam registrados em FAMILIAS_SEM_ORING;
- 1330: possui 2 O-rings da tampa + 1 do carretel; o grupo pequeno
  (1/2" e 3/4") usa O-ring de tampa diferente do grupo grande (1");
- 1342: NBR/Buna-N usa O-ring do pistão (G5). FKM, EPDM e PTFE usam aro
  do pistão, que pertence ao sistema G3 e não deve ser tratado como O-ring;
- 1360: o O-ring do anticorpo pertence a um conjunto exclusivo chamado
  anticorpo. Seus componentes não devem ser desmembrados até a regra
  específica da família ser definida.
"""

FAMILIAS_SEM_ORING = {
    "1312", "1327", "1335", "1339", "1356", "1365", "1393",
    "2012", "2024", "2041", "2088", "3014", "3010", "V171",
    "1317", "2017", "2049", "1340", "1376", "1380",
}

MAPA_ORINGS_FAMILIA = {
    "1314": [("tampa", 1)],
    "1323": [("torre", 1)],
    "1325": [("tampa", 1), ("carretel", 1)],
    "1330": [("tampa", 2), ("carretel", 1)],
    "1342": [("tampa", 1), ("torre", 1)],
    "1343": [("tampa", 1)],
    "1344": [("tampa", 1), ("torre", 1)],
    "1351": [("tampa", 1), ("pistao", 1)],
    "1360": [("anticorpo", 1)],
    "1375": [("corpo", 1)],
    "1387": [("corpo", 1)],
    "1388": [("tampa", 1), ("corpo", 1)],
    "1390": [("tampa", 1), ("corpo", 1)],
    "1397": [("corpo", 1), ("pistao", 1), ("tampa", 1)],
    "2026": [("torre", 1)],
    "2030": [("tampa", 1), ("carretel", 1)],
    "2036": [("torre", 1)],
    "2050": [("tampa", 1), ("pistao", 1)],
    "2051": [("tampa", 1), ("pistao", 1)],
    "2073": [("torre", 1)],
    "2094": [("tampa", 1)],
    "2095": [("torre", 1)],
    "3073": [("torre", 1)],
}

GRUPOS_ORING_TAMPA_1330 = {
    "PEQUENO": {"1/2", "3/4"},
    "GRANDE": {"1"},
}


def _normalizar(valor):
    if valor is None:
        return None
    return str(valor).strip().upper()


def _normalizar_tamanho(tamanho):
    valor = _normalizar(tamanho)
    equivalencias = {
        '1/2"': "1/2", "1/2": "1/2",
        '3/4"': "3/4", "3/4": "3/4",
        '1"': "1", "1": "1",
    }
    return equivalencias.get(valor, valor)


def _eh_nbr(vedacao):
    valor = _normalizar(vedacao)
    return valor in {"A", "NBR", "BUNA-N", "BUNA N", "BUNA-N (NBR)"}


def identificar_orings(familia, vedacao=None, tamanho=None):
    """Retorna somente O-rings confirmados para a família/configuração."""
    familia = _normalizar(familia)

    if familia in FAMILIAS_SEM_ORING:
        return []

    componentes = []

    for local, quantidade in MAPA_ORINGS_FAMILIA.get(familia, []):
        item = {
            "tipo": "O-ring",
            "local": local,
            "quantidade": quantidade,
            "familia": familia,
        }

        if familia == "1330" and local == "tampa":
            tamanho_normalizado = _normalizar_tamanho(tamanho)
            if tamanho_normalizado in GRUPOS_ORING_TAMPA_1330["PEQUENO"]:
                item["grupo_tamanho"] = "PEQUENO_1/2_3/4"
            elif tamanho_normalizado in GRUPOS_ORING_TAMPA_1330["GRANDE"]:
                item["grupo_tamanho"] = "GRANDE_1"

        componentes.append(item)

    if familia == "1342" and _eh_nbr(vedacao):
        componentes.append({
            "tipo": "O-ring",
            "local": "pistao",
            "quantidade": 1,
            "familia": familia,
            "regra": "SOMENTE_NBR_BUNA_N",
        })

    return componentes
