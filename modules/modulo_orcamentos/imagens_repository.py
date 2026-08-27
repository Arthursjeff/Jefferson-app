from urllib.parse import quote

from core import config


BUCKET_IMAGENS = "imagens-produtos"


def obter_url_imagem(nome_arquivo):

    if not nome_arquivo:
        return None

    nome_codificado = quote(
        str(nome_arquivo),
        safe="/"
    )

    return (
        f"{config.SUPABASE_URL}"
        f"/storage/v1/object/public/"
        f"{BUCKET_IMAGENS}/"
        f"{nome_codificado}"
    )
