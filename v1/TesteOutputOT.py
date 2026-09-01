from funcoesOT import (
    busca_id,
    busca_historico,
    checagem,
    num_br
)

codigo_if = "CRA02300TMS"
"""Data do evento (dd/mm/yyyy): """
data_evento = "13/08/2026"
amort_ord_per = num_br(" 0  ")
amex_per = num_br("   0   ")
juros_per = num_br("100")
incorp_per = num_br("0")

# 1. Tratamento para caso o código não seja encontrado
res_id = busca_id(codigo_if)
if not res_id:
    print("Erro: Título não encontrado na Oliveira Trust.")
    exit()

id_ot, nome_titulo = res_id
print(f"\nTítulo encontrado: {nome_titulo} (código {codigo_if})")

dados_evento = busca_historico(id_ot, data_evento)

if dados_evento is None:
    print("Nenhum evento encontrado nessa data.")
else:
    # Desempacota os 7 valores retornados por busca_historico
    vn, juros, pu, amort_pgto, juros_pgto, premio_pgto, total_pgto = dados_evento
    
    # 2. Chamada segura usando parâmetros nomeados
    resultado = checagem(
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
    
    # 3. Iteração correta sobre a lista "detalhes" do dicionário
    print(f"\n=== STATUS GERAL: {resultado['status_geral']} ===")
    for d in resultado["detalhes"]:
        print(f"[{d['status']}] {d['item']} | Calc: {d['calculado']} | Esp: {d['esperado']} | {d['msg']}")