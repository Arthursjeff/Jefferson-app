import pandas as pd


MAPA_COLUNAS = {
    "Código": "codigo_cliente",
    "Razão Social/Nome": "razao_social",
    "Nome Fantasia": "nome_fantasia",
    "Código Classificação": "codigo_classificacao",

    "Código País": "codigo_pais",
    "Cidade": "cidade",
    "Endereço": "endereco",
    "Número": "numero",
    "Complemento": "complemento",
    "Bairro": "bairro",
    "Cep": "cep",
    "Estado": "estado",

    "Telefone": "telefone",
    "Telefone 2": "telefone_secundario",
    "Celular": "celular",

    "Pessoa (Física/Juridica)": "tipo_pessoa",
    "ID Inscrição estadual": "id_inscricao_estadual",
    "Cnpj/Cpf": "cnpj_cpf",
    "Inscrição Estadual": "inscricao_estadual",

    "Última Compra": "ultima_compra",

    # ATENÇÃO:
    # No ERP aparece como Código Vendedor,
    # mas no Jefferson App representa o tipo de cliente.
    "Código Vendedor": "tipo_cliente_codigo",

    "Cliente Desde": "cliente_desde",
    "Email": "email",

    "Simples Nacional?": "simples_nacional",
    "SUFRAMA": "suframa",
}


TIPOS_CLIENTE = {
    "100": "BIANCA-VEND INTERNA",
    "66": "DIRETO-CONSUMIDOR FINAL",
    "65": "DIRETO-FABRI FORA SP",
    "8": "DIRETO-FABRICANTE SP",
    "9": "DISTRIBUIDOR GERAL",
    "6": "ENGENHARIAS/PROJETOS",
    "30": "FERNANDO VENDEDOR",
    "110": "GRANDES NEGOCIOS",
    "300": "JAQUE/RITA/MARCELO-VEND INTER",
    "20": "MANUTENCAO/INSTALACAO",
    "200": "MARILENE-VEND INTERN",
    "1": "REG I -",
    "2": "REG II -",
    "3": "REG III - VEND 3",
    "4": "REG IV -",
    "5": "REG V - INTERIOR SÃO PAULO",
    "44": "REGIAO 4.4",
    "51": "REGIAO 5.1",
    "52": "REGIAO 5.2",
    "11": "REPRES RS - BONI",
    "12": "REPRES SC -",
    "7": "REVENDA - BRASIL",
    "701": "REVENDA G SÃO PAULO",
    "702": "REVENDA INTERIOR SP",
    "155": "VENDA POR REPRESENTAÇÃO",
}


def limpar_nome_coluna(nome):
    """
    Remove espaços extras do nome da coluna.
    """
    return str(nome).strip()


def texto_limpo(valor):
    """
    Converte valores do Excel para texto limpo.
    Valores vazios continuam vazios.
    """

    if pd.isna(valor):
        return None

    valor = str(valor).strip()

    if valor == "":
        return None

    # Excel frequentemente converte códigos numéricos para 123.0
    if valor.endswith(".0"):
        valor = valor[:-2]

    return valor


def normalizar_booleano(valor):
    """
    Converte diferentes formas de SIM/NÃO para True/False.
    """

    if pd.isna(valor):
        return None

    texto = str(valor).strip().upper()

    if texto in ["SIM", "S", "1", "TRUE", "VERDADEIRO", "X"]:
        return True

    if texto in ["NAO", "NÃO", "N", "0", "FALSE", "FALSO"]:
        return False

    return None


def normalizar_data(valor):
    """
    Converte datas do Excel para YYYY-MM-DD.
    """

    if pd.isna(valor):
        return None

    data = pd.to_datetime(valor, errors="coerce", dayfirst=True)

    if pd.isna(data):
        return None

    return data.strftime("%Y-%m-%d")


def preparar_clientes(arquivo_excel):

    # Lê o Excel bruto
    df_original = pd.read_excel(
        arquivo_excel,
        dtype=object
    )

    # Remove espaços extras dos nomes das colunas
    df_original.columns = [
        limpar_nome_coluna(coluna)
        for coluna in df_original.columns
    ]

    quantidade_colunas_original = len(df_original.columns)
    quantidade_linhas_original = len(df_original)

    # Descobre quais colunas esperadas realmente existem
    colunas_encontradas = [
        coluna
        for coluna in MAPA_COLUNAS.keys()
        if coluna in df_original.columns
    ]

    colunas_nao_encontradas = [
        coluna
        for coluna in MAPA_COLUNAS.keys()
        if coluna not in df_original.columns
    ]

    # Seleciona apenas as colunas que queremos
    df = df_original[colunas_encontradas].copy()

    # Renomeia para o padrão do Supabase
    df = df.rename(columns=MAPA_COLUNAS)

    # -----------------------------------------
    # LIMPEZA DOS CAMPOS DE TEXTO
    # -----------------------------------------

    campos_texto = [
        "codigo_cliente",
        "razao_social",
        "nome_fantasia",
        "codigo_classificacao",
        "codigo_pais",
        "cidade",
        "endereco",
        "numero",
        "complemento",
        "bairro",
        "cep",
        "estado",
        "telefone",
        "telefone_secundario",
        "celular",
        "tipo_pessoa",
        "id_inscricao_estadual",
        "cnpj_cpf",
        "inscricao_estadual",
        "tipo_cliente_codigo",
        "email",
        "suframa",
    ]

    for coluna in campos_texto:
        if coluna in df.columns:
            df[coluna] = df[coluna].apply(texto_limpo)

    # -----------------------------------------
    # DATAS
    # -----------------------------------------

    if "ultima_compra" in df.columns:
        df["ultima_compra"] = df["ultima_compra"].apply(
            normalizar_data
        )

    if "cliente_desde" in df.columns:
        df["cliente_desde"] = df["cliente_desde"].apply(
            normalizar_data
        )

    # -----------------------------------------
    # BOOLEANOS
    # -----------------------------------------

    if "simples_nacional" in df.columns:
        df["simples_nacional"] = df[
            "simples_nacional"
        ].apply(normalizar_booleano)

    # -----------------------------------------
    # TIPO DE CLIENTE
    # -----------------------------------------

    if "tipo_cliente_codigo" in df.columns:

    # Código 0 no ERP significa "sem classificação"
        df.loc[
            df["tipo_cliente_codigo"] == "0",
            "tipo_cliente_codigo"
        ] = None

        df["tipo_cliente"] = df[
            "tipo_cliente_codigo"
        ].map(TIPOS_CLIENTE)

    # Só marca como NÃO MAPEADO quando existe um código real
    # que ainda não está na nossa tabela de tipos
        df.loc[
            df["tipo_cliente_codigo"].notna()
            & df["tipo_cliente"].isna(),
            "tipo_cliente"
        ] = "NÃO MAPEADO"

    # -----------------------------------------
    # REMOVE LINHAS SEM CÓDIGO
    # -----------------------------------------

    if "codigo_cliente" in df.columns:

        antes = len(df)

        df = df[
            df["codigo_cliente"].notna()
        ].copy()

        linhas_sem_codigo = antes - len(df)

    else:
        linhas_sem_codigo = quantidade_linhas_original

    # -----------------------------------------
    # RELATÓRIO
    # -----------------------------------------

    codigos_nao_mapeados = []

    if (
        "tipo_cliente" in df.columns
        and "tipo_cliente_codigo" in df.columns
    ):
        codigos_nao_mapeados = (
            df.loc[
                df["tipo_cliente"] == "NÃO MAPEADO",
                "tipo_cliente_codigo"
            ]
            .dropna()
            .unique()
            .tolist()
        )

    relatorio = {
        "linhas_original": quantidade_linhas_original,
        "linhas_processadas": len(df),
        "linhas_sem_codigo": linhas_sem_codigo,
        "colunas_original": quantidade_colunas_original,
        "colunas_utilizadas": len(colunas_encontradas),
        "colunas_encontradas": colunas_encontradas,
        "colunas_nao_encontradas": colunas_nao_encontradas,
        "codigos_tipo_cliente_nao_mapeados": codigos_nao_mapeados,
    }

    return df, relatorio

def dataframe_para_registros(df):
    """
    Converte o DataFrame tratado em uma lista de dicionários
    compatível com o Supabase.

    Garante que valores vazios sejam enviados como NULL.
    """

    df_envio = df.copy()

    # Converte NaN / NaT / pd.NA para None
    df_envio = df_envio.astype(object).where(
        pd.notna(df_envio),
        None
    )

    return df_envio.to_dict(orient="records")
