from scrapers.vortx import busca_id_vortx, busca_historico_vortx
from scrapers.oliveira_trust import busca_id_oliveira, busca_historico_oliveira
import requests
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

app = Flask(__name__)

load_dotenv("user.env")
TOKEN = os.getenv("FTRADER_TOKEN")

MAX_WORKERS = 5
TOLERANCIA = 0.01


def buscar_pu_referencia(cod_ativo: str, data: str, token: str):
    """
    Busca o PU (ValorPUPAR) de um ativo numa data específica no FTrader.
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


def buscar_pu_oliveira(cod_ativo: str, data: str,cache_id:dict,cache_lock):
    """
    Busca o PU no Oliveira Trust pra um ativo numa data específica.
    Retorna o PU ou None se não achar o ativo/histórico.
    """
    with cache_lock:
        id_cacheado=cache_id.get(cod_ativo)

    if id_cacheado is None:
        resultado_id = busca_id_oliveira(cod_ativo)
        if resultado_id is None:
            return None

        id_ot,titulo = resultado_id

        with cache_lock:
            cache_id[cod_ativo]=id_ot

    else:
        id_ot=id_cacheado

    resultado = busca_historico_oliveira(id_ot, data)
    if resultado is None:
        return None

    return resultado[2]


def buscar_pu_vortx(cod_ativo: str, data: str, cache_id: dict, cache_lock):
    # Verifica o cache primeiro, protegido pelo Lock
    with cache_lock:
        id_cacheado = cache_id.get(f"vortx_{cod_ativo}")

    if id_cacheado is None:
        resultado_id = busca_id_vortx(cod_ativo)
        if resultado_id is None:
            return None
            
        id_ot = resultado_id
        # Salva no cache
        with cache_lock:
            cache_id[f"vortx_{cod_ativo}"] = id_ot
    else:
        id_ot = id_cacheado

    resultado = busca_historico_vortx(id_ot, data)
    
    if resultado is None:
        return None

    return resultado["unitPriceEmpty"]


def processar_item(cod_ativo_i, data_i, cache_id, cache_lock):
    item = {"codAtivo": cod_ativo_i, "data": data_i}

    try:
        pu_informado = buscar_pu_oliveira(cod_ativo_i, data_i, cache_id, cache_lock)

        if pu_informado is None:
            pu_informado = buscar_pu_vortx(cod_ativo_i, data_i, cache_id, cache_lock)
            if pu_informado is None:
                item["status"] = "erro"
                item["erro"] = "PU não encontrado em nenhum AF"
                return item

        pu_informado = float(pu_informado)

        pu_referencia = buscar_pu_referencia(cod_ativo_i, data_i, TOKEN)

        if pu_referencia is None:
            item["status"] = "erro"
            item["erro"] = "nenhum PU encontrado no FTrader"
            return item

        diferenca = round(abs(pu_informado - pu_referencia), 6)

        item["pu_agente_fiduciario"] = pu_informado
        item["pu_ftrustee"] = pu_referencia
        item["diferenca"] = diferenca
        item["bateu"] = diferenca <= TOLERANCIA

    except (TypeError, ValueError):
        item["status"] = "erro"
        item["erro"] = "PU retornado pelo AF não é um número válido"
    except requests.exceptions.RequestException as e:
        item["status"] = "erro"
        item["erro"] = f"falha ao consultar o FTrader: {str(e)}"
    except Exception as e:
        item["status"] = "erro"
        item["erro"] = f"erro inesperado: {str(e)}"

    return item



@app.route("/verificar-pu", methods=["POST"])
def verificar_pu():
    dados = request.get_json()

    if dados is None:
        return jsonify({"erro": "envie um JSON no body da requisição"}), 400

    cod_ativo = dados.get("codAtivo")
    data = dados.get("data")

    if not cod_ativo or not data:
        return jsonify({"erro": "informe 'codAtivo' e 'data' (YYYY-MM-DD)"}), 400

    if not isinstance(cod_ativo, list) or not isinstance(data, list):
        return jsonify({"erro": "'codAtivo' e 'data' devem ser listas []"}), 400

    if len(cod_ativo) != len(data):
        return jsonify({
            "erro": "'codAtivo' e 'data' devem possuir a mesma quantidade de elementos"
        }), 400

    cache_id={}
    cache_lock=Lock()

    resultados=[None]*len(cod_ativo)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(processar_item, cod_ativo[i], data[i], cache_id, cache_lock): i
            for i in range(len(cod_ativo))
        }
        for future in as_completed(futures):
            i = futures[future]
            resultados[i] = future.result()

    return jsonify(resultados), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)