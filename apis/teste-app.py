import requests
import os
from dotenv import load_dotenv

load_dotenv("user.env")
token=os.getenv("FTRADER_TOKEN")

BASE_URL = "https://ftrader.com.br/apiFincs/api/pagamento/GetPUPARs"
cod_ativo="19C0127869"

def buscar_pu_referencia(cod_ativo: str, data: str, token: str):
    """
    Busca o PU (ValorPUPAR) de um ativo numa data específica.
    data no formato 'YYYY-MM-DD'.
    Retorna o valor do PU ou None se não achar registro na data.
    """
    resp = requests.get(
        BASE_URL,
        params={"codAtivo": cod_ativo},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30
    )
    resp.raise_for_status()
    lista = resp.json()
 
    for registro in lista:
        # "Data" vem como "2023-03-14T00:00:00", comparamos só a parte da data
        if registro.get("Data", "").startswith(data):
            return registro.get("ValorPUPAR")

    
    return None

print(buscar_pu_referencia(cod_ativo,"2020-07-29",token))