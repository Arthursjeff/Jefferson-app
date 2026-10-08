"""Regras técnicas G1: torre externa e componentes internos.

Torre externa nunca pertence ao kit de reparo. As identidades abaixo são
lógicas, não códigos de fabricação. Z/INA podem alterar componentes internos.
"""
def normalizar(v):
    return str(v or "").strip().upper().replace("LATÃO","LATAO")

def resolver_g1(familia, material=None, estado=None, construcao=None, vedacao=None, final=None, bitola=None):
    f=normalizar(familia)
    m=normalizar(material)
    e=normalizar(estado)
    c=normalizar(construcao)
    v=normalizar(vedacao)
    t=normalizar(final)
    b=normalizar(bitola)
    z="Z" in c
    ina="INA" in c or e=="INA"
    forma=("Z_INA" if z and ina else "Z" if z else "INA" if ina else "REGULAR")
    grupo = "1312_2012" if f in {"1312","2012"} else "2026_2036" if f in {"2026","2036"} else f
    if f=="2036" and b in {"12","1 1/2", '1 1/2"'}:
        grupo_torre="GENERICO"
    else:
        grupo_torre=grupo
    if f=="1335" and m=="INOX" and b in {"04","06",'1/2"','3/4"',"1/2","3/4"}:
        tamanho_interno="MEIO_TRES_QUARTOS"
    else:
        tamanho_interno=b or None
    if f=="1323" and t not in {"C","A","D","U"}:
        # Não inferir final a partir de vedação sem regra confirmada.
        final_pendente=True
    else:
        final_pendente=False
    interno={"grupo":grupo,"construcao":forma,"vedacao":v or None}
    if f=="1323":
        interno["final"]=t or None
    if f=="1335" and m=="INOX":
        interno["tamanho"]=tamanho_interno
    if f in {"2026","2036"}:
        interno["grupo"]="2026_2036"
    nucleo_grupo="1365_EXCLUSIVO" if f=="1365" else "ACHATADO_COMPARTILHADO" if f in {"1330","2030","1325"} else interno["grupo"]
    achatado=f in {"1330","2030","1325","1365"}
    tem_carretel=f in {"1330","2030","1325"}
    # Identidade das molas considera o material, mesmo quando o formato é compartilhado.
    mola_material="INOX 304" if m=="INOX" else "INOX 303" if m=="LATAO" else None
    componentes={
        "nucleo_movel":{"grupo":nucleo_grupo,"formato":"ACHATADO" if achatado else "REGULAR","material":"INOX 430FR","vedacao":v or None,"construcao":forma},
        "assento":{"grupo":interno["grupo"],"material":v or None,"final":t or None if f=="1323" else None},
        "mola_nucleo":{"grupo":interno["grupo"],"material":mola_material,"construcao":forma},
    }
    if achatado:
        componentes["cadeirinha"]={"grupo":interno["grupo"],"construcao":forma}
        componentes["mola_cadeirinha"]={"grupo":"1365" if f=="1365" else "1330_2030_ESPECIAL" if f in {"1330","2030"} else "1325","final":t or None if f=="1365" else None}
    if tem_carretel:
        componentes["carretel"]={"grupo":"1330_2030" if f in {"1330","2030"} else "1325"}
    return {
        "grupo_componente":"G1",
        "familia":f,
        "torre_externa":{"grupo":grupo_torre,"material":m or None,"construcao":forma,"fora_kit_reparo":True},
        "componentes_internos":componentes,
        "kit_reparo_exclui_torre_externa":True,
        "validacao_pendente":(["FINAL_1323"] if final_pendente else []),
    }
