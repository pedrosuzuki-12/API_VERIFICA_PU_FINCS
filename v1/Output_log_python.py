from funcoes_aux import num_br

from funcoesVT import (
    busca_id_vortx,
    busca_historico_vortx,
    checagem_vortx,
)

from funcoesOT import (
    busca_id_oliveira,
    busca_historico_oliveira,
    checagem_oliveira,
)
import pandas as pd

df = pd.read_excel('TesteOTInput.xlsx', sheet_name=0, usecols="A:H")
df = df.dropna(subset=[df.columns[0]])

resultados_export = []

for index, row in df.iterrows():
    codigo_if = str(row.iloc[0]).strip()
    data_evento = pd.to_datetime(row.iloc[1]).strftime('%Y-%m-%d')
    amort_ord_per = num_br(row.iloc[2])
    amex_per = num_br(row.iloc[3])
    juros_per = num_br(row.iloc[4])
    incorp_per = num_br(row.iloc[6])
    af = str(row.iloc[7]).strip().upper()
    if af=="OLIVEIRA TRUST DTVM S.A.":

    # 1. Tratamento para caso o código não seja encontrado
        res_id = busca_id_oliveira(codigo_if)
        if not res_id:
            print(f"Erro: Título {codigo_if} não encontrado na Oliveira Trust. Pulando para o próximo...")
            resultados_export.append({
                "Codigo": codigo_if,
                "Data": data_evento,
                "Agente": "Oliveira Trust",
                "Log": "Título não encontrado na Oliveira Trust"
            })
            continue

        id_ot, nome_titulo = res_id
    
        print(f"\nTítulo encontrado: {nome_titulo} (código {codigo_if})")

        dados_evento = busca_historico_oliveira(id_ot, data_evento)

        if dados_evento is None:
            print(f"Nenhum evento encontrado na data {data_evento}.")
        else:
            # Desempacota os 7 valores retornados por busca_historico
            vn, juros, pu, amort_pgto, juros_pgto, premio_pgto, total_pgto = dados_evento
    
        # 2. Chamada segura usando parâmetros nomeados
            resultado = checagem_oliveira(
                amort_ord_per=amort_ord_per,
                amex_per=amex_per,
                incorp_per=incorp_per,
                vn=vn,
                juros=juros,
                pu=pu,
                amort_pgto=amort_pgto,
                juros_pgto=juros_pgto,
                premio_pgto=premio_pgto,
                total_pgto=total_pgto,
                juros_per=juros_per
            )
    
            print(f"Log Resumo: {resultado['log_suscinto']}")
            resultados_export.append({
                "Codigo": codigo_if,
                "Data": data_evento,
                "Agente": "Oliveira Trust",
                "Log": resultado["log_suscinto"]
            })


    elif af == "VORTX DTVM LTDA.":
        res_id = busca_id_vortx(codigo_if)
        if not res_id:
            print(f"Erro: Título {codigo_if} não encontrado na Vórtx. Pulando para o próximo...")
            resultados_export.append({
                "Codigo": codigo_if,
                "Data": data_evento,
                "Agente": "Vórtx",
                "Log": "Título não encontrado na Vórtx"
            })
            continue 

        id_vortx = res_id

        print(f"\nTítulo encontrado: (código {codigo_if})")

        dados_evento = busca_historico_vortx(id_vortx, data_evento)

        if dados_evento is None:
            print(f"⚠️  Nenhum evento encontrado no histórico para a data {data_evento}.")
            resultados_export.append({
                "Codigo": codigo_if,
                "Data": data_evento,
                "Agente": "Vórtx",
                "Log": "Nenhum evento encontrado na data"
            })
            continue

        resultado = checagem_vortx(
        amort_ord_per=amort_ord_per,
        amex_per=amex_per,
        juros_per=juros_per,
        incorp_per=incorp_per,
        linha=dados_evento
        )

        print(f"Log Resumo: {resultado['log_suscinto']}")
        resultados_export.append({
            "Codigo": codigo_if,
            "Data": data_evento,
            "Agente": "Vórtx",
            "Log": resultado["log_suscinto"]
        })




    