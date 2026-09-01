import re
import requests
from bs4 import BeautifulSoup
import io
import pandas as pd
import math
from utils.formatters import num_br


TOLERANCIA = 0.0001


def busca_id_vortx(codigo_cetip: str):
    url = f"https://www.vortx.com.br/investidor/dcm?busca={codigo_cetip}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Faz o parse do HTML retornado pelo servidor
        soup = BeautifulSoup(response.text, "html.parser")

        # Procura por qualquer link (href) que contenha "/investidor/dcm/operacao?id="
        link = soup.find("a", href=re.compile(r"/investidor/dcm/operacao\?id=\d+"))

        if link and "href" in link.attrs:
            # Extrai apenas os números após o 'id='
            match = re.search(r"id=(\d+)", link["href"])
            if match:
                return match.group(1)

        return None

    except requests.RequestException as e:
        print(f"Erro ao acessar o site da Vórtx: {e}")
        return None


def busca_historico_vortx(id_operacao: str,data_evento: str)-> pd.Series | None:
    url = (
        "https://apis.vortx.com.br/vxsite/api/operacao/"
        f"{id_operacao}/preco-unitario/historico-pagamentos"
    )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.vortx.com.br",
        "Referer": "https://www.vortx.com.br/",
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        dados = response.json()

        if not dados.get("success") or "unitPrices" not in dados:
            print("A API não retornou a lista 'unitPrices'.")
            return None

        l=dados["unitPrices"][-50:]
        df_pu = pd.DataFrame(l)


        if "paymentDate" in df_pu.columns:
            df_pu["paymentDate"] = pd.to_datetime(df_pu["paymentDate"])
            df_pu = df_pu.sort_values(by="paymentDate", ascending=False).reset_index(drop=True)
            df_pu["paymentDate"] = df_pu["paymentDate"].dt.strftime("%Y-%m-%d") 

            colunas_uteis = [
                "nominalValue", "paymentDate", "interest", 
                "amortization", "total", "unitPriceFull", "unitPriceEmpty"
            ]
            df_pu = df_pu[[col for col in colunas_uteis if col in df_pu.columns]]
            
            # Encontra o índice (linha) da data do evento
            indices = df_pu.index[df_pu["paymentDate"] == data_evento].tolist()

            if not indices:
                print(f"Data {data_evento} não encontrada no histórico recente.")
                return None

            idx_evento = indices[0]
            linha = df_pu.iloc[idx_evento].copy()

            #Busca o Valor Nominal da data anterior (índice seguinte na tabela ordenada)
            if idx_evento + 1 < len(df_pu):
                linha["nominalValueAnterior"] = float(df_pu.iloc[idx_evento + 1]["nominalValue"])
            else:
                linha["nominalValueAnterior"] = float(linha["nominalValue"])

            return linha

    except requests.RequestException as e:
        print(f"Erro ao conectar com a API da Vórtx: {e}")
        return None
    except ValueError:
        print("Erro ao decodificar a resposta JSON.")
        return None



def checagem_vortx(
    amort_ord_per: float,
    amex_per: float,
    juros_per: float,
    incorp_per: float,
    linha: dict | pd.Series
):

    esp_amort_ord = num_br(amort_ord_per)
    esp_amex = num_br(amex_per)
    esp_incorp = num_br(incorp_per)
    esp_juros = num_br(juros_per)

    if linha is None:
        return {"log_suscinto": "Sem evento na data escolhida ou Não pagou nada"}

    # Get values
    vlr_nominal = float(linha["nominalValue"])
    total_pago = float(linha["total"])
    amort_paga = float(linha["amortization"])

    # 1. Calculate Real Amortization
    amort_real = (amort_paga / vlr_nominal) * 100.0 if vlr_nominal > 0 and amort_paga > 0 else 0.0
    amort_esperada = esp_amort_ord + esp_amex

    # 2. Calculate Real Incorporação
    incorp_real = 0.0
    if total_pago <= 0 and esp_incorp > 0:
        # If no payment is made and some incorporacao is expected, it usually means 100% incorporacao
        incorp_real = 100.0
    elif esp_incorp > 0 and esp_incorp != 100.0:
        # If partial incorporação is expected, calculate the unpaid portion of ordinary amortization
        incorp_real = max(0.0, esp_amort_ord - amort_real)
    elif total_pago <= 0 and esp_incorp == 0 and amort_esperada > 0:
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
        log_suscinto = f"DIVERGÊNCIA - " + " | ".join(divergencias).replace(".", ",")

    return {"log_suscinto": log_suscinto}
