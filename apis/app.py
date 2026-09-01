from utils.formatters import num_br
from scrapers.vortx import (
    busca_id_vortx,
    busca_historico_vortx,
)
from scrapers.oliveira_trust import (
    busca_id_oliveira,
    busca_historico_oliveira,
)

import requests
import os
from dotenv import load_dotenv

load_dotenv("user.env")
token=os.getenv("FTRADER_TOKEN")

cod_ativo="19C0127869"
data="22-10-20"

def buscar_pu_referencia(cod_ativo: str, data: str, token: str):
    """
    Busca o PU (ValorPUPAR) de um ativo numa data específica.
    data no formato 'YYYY-MM-DD'.
    Retorna o valor do PU ou None se não achar registro na data.
    """
    resp = requests.get(
        "https://ftrader.com.br/apiFincs/api/pagamento/GetPUPARs",
        params={"codAtivo": cod_ativo},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30
    )
    resp.raise_for_status()
    lista = resp.json()
 
    for registro in lista:
        # "Data" vem como "2023-03-14T00:00:00", compara só a parte da data
        if registro.get("Data", "").startswith(data):
            return registro.get("ValorPUPAR")

    
    return None

try:
    id_ot, _ = busca_id_oliveira(cod_ativo)
    if id_ot:
        resultado = busca_historico_oliveira(id_ot, data)
        if resultado:
            pu = resultado[2]
            print(f"PU: {pu}")
        else:
            print("Resultado não encontrado no histórico.")
    else:
        print("Ativo não encontrado na Oliveira Trust.")
except Exception as e:
    print(f"Erro: {e}")