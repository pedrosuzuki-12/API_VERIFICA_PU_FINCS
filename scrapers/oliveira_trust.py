import requests
import math
import pandas as pd
from datetime import datetime
from utils.formatters import num_br

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.oliveiratrust.com.br/",
    "Origin": "https://www.oliveiratrust.com.br",
    "Accept": "application/json, text/plain, */*",
}

TOLERANCIA = 0.0001


def busca_id_oliveira(codigo_if):
    url_raw="https://services-ft.oliveiratrust.com.br/app/v1/titulos?busca="
    url=url_raw+codigo_if
    try:
        resposta = requests.get(url, headers=headers,timeout=10)
        resposta.raise_for_status()
    except requests.RequestException as e:
        print(f"Erro na requisição: {e}")
        return None
    
    try:
        dados=resposta.json()
        lista_id = dados.get("data", [])
        
        if not lista_id:
            print("Nenhum título encontrado para o código informado!")
            return None
        
        id=lista_id[0]
        return id.get("tit"),id.get("titulo")
    except (ValueError,KeyError) as e:
        print(f"Erro ao processar dados do JSON: {e}")
        return None

def busca_historico_oliveira(id_ot,data_evento):


    url=f"https://services-ft.oliveiratrust.com.br/app/v1/titulos/historico_pu/{id_ot}?page=1&limit=50"
    try:
        resposta=requests.get(url,headers=headers,timeout=10)

        if resposta.status_code != 200:
            print(f"Erro: HTTP {resposta.status_code}: {resposta.text[:200]}")
            return None
        
        dados=resposta.json()
    except (requests.RequestException,ValueError) as e:
        print(f"Erro de conexão ou JSON inválido: {e}")
        return None
    
    bloco_data=dados.get("data",{})
    if not isinstance(bloco_data,dict):
        print("Estrutura do JSON mudou: chave 'data externa não é um objeto")
        return None

    infos=bloco_data.get("data",[])
    if not isinstance(infos,list):
        print("Estrutura do JSON mudou: chave 'data interna não é uma lista")
        return None
    
    for item in infos:
        if isinstance(item, dict):
            data_item=item.get("data")

            if data_item==data_evento:
                return (
                num_br(item.get("valor_nominal")),
                num_br(item.get("juros")),
                num_br(item.get("pu")),
                num_br(item.get("amort_pgto")),
                num_br(item.get("juros_pgto")),
                num_br(item.get("premio_pgto")),
                num_br(item.get("total_pgto")),
        )
    return None


def checagem_oliveira(
    amort_ord_per,
    amex_per,
    incorp_per,
    vn,
    juros,
    pu,
    amort_pgto,
    juros_pgto,
    premio_pgto,
    total_pgto,
    juros_per=100.0
):
    """
    Realiza a checagem das regras de amortização, juros, incorporação, prêmio e PU.
    Retorna apenas o log_suscinto.
    """
    esp_amort_ord = num_br(amort_ord_per)
    esp_amex = num_br(amex_per)
    esp_incorp = num_br(incorp_per)
    esp_juros = num_br(juros_per)

    # 1. Calculate Real Amortization
    amort_real = (amort_pgto / vn) * 100.0 if vn > 0 and amort_pgto > 0 else 0.0
    amort_esperada = esp_amort_ord + esp_amex

    # 2. Calculate Real Incorporação
    incorp_real = 0.0
    if total_pgto <= 0 and esp_incorp > 0:
        # If no payment is made and some incorporacao is expected, it usually means 100% incorporacao
        # Or we just set it to what was calculated as unpaid
        incorp_real = 100.0
    elif esp_incorp > 0 and esp_incorp != 100.0:
        # If partial incorporação is expected, calculate the unpaid portion of ordinary amortization
        incorp_real = max(0.0, esp_amort_ord - amort_real)
    elif total_pgto <= 0 and esp_incorp == 0 and amort_esperada > 0:
        # If no payment but we expected amortization, this might be 100% incorporacao implicitly
        incorp_real = 100.0

    # Determine real AMEX vs Ord for logging
    if math.isclose(amort_real, amort_esperada, abs_tol=TOLERANCIA):
        amort_ord_real = esp_amort_ord
        amex_real = esp_amex
    else:
        # If there's a difference, allocate to AMEX first if amort_real > ord expected
        if amort_real > esp_amort_ord:
            amort_ord_real = esp_amort_ord
            amex_real = amort_real - esp_amort_ord
        else:
            amort_ord_real = amort_real
            amex_real = 0.0

    # 3. Check for divergences
    status_geral = "OK"
    divergencias = []

    if not math.isclose(amort_real, amort_esperada, abs_tol=TOLERANCIA):
        status_geral = "DIVERGENTE"
        divergencias.append(f"Amort. Total Real ({amort_real:.8f}%) != Esperada ({amort_esperada:.8f}%)")
        
    if esp_incorp > 0 and not math.isclose(incorp_real, esp_incorp, abs_tol=TOLERANCIA):
        status_geral = "DIVERGENTE"
        divergencias.append(f"Incorp. Real ({incorp_real:.8f}%) != Esperada ({esp_incorp:.8f}%)")

    # 4. Generate Log
    amort_ord_real_str = str(round(amort_ord_real, 8)).replace(".", ",")
    amex_real_str = str(round(amex_real, 8)).replace(".", ",")
    incorp_real_str = str(round(incorp_real, 8)).replace(".", ",")

    if status_geral == "OK":
        log_suscinto = (
            f"OK (Amort. Ordinária: {amort_ord_real_str}% | AMEX: {amex_real_str}% | "
            f"Incorporação: {incorp_real_str}%)"
        )
    else:
        # Include exactly what diverged
        log_suscinto = f"DIVERGÊNCIA - " + " | ".join(divergencias).replace(".", ",")

    return {"log_suscinto": log_suscinto}





