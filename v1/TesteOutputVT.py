# =====================================================================
# 0. IMPORTAÇÕES DO MÓDULO DE FUNÇÕES
# =====================================================================
from funcoesVT import (
    buscar_id_cetip,
    capturar_pu_via_api,
    checagem_valores,
    num_br 
)

# =====================================================================
# 1. PARÂMETROS DE ENTRADA (CONFIGURAÇÃO DO EVENTO)
# =====================================================================
codigo_if = "21C0663319"
data_evento = "06/07/2026"  # Formato: dd/mm/yyyy
amort_ord_per = num_br("      0      ")
amex_per      = num_br("   0000000      ")
juros_per     = num_br("100,000000000000")
incorp_per    = num_br("  0   ")

# =====================================================================
# 2. BUSCA E VALIDAÇÃO DO ATIVO
# =====================================================================
res_id = buscar_id_cetip(codigo_if)

if not res_id:
    print(f"❌ Erro: Título (código {codigo_if}) não encontrado no portal da Vórtx.")
    exit()

id_vortx = res_id
print(f"\n✅ Título encontrado | Código: {codigo_if}")

# =====================================================================
# 3. CAPTURA DE DADOS NA API
# =====================================================================
dados_evento = capturar_pu_via_api(id_vortx, data_evento)

if dados_evento is None:
    print(f"⚠️  Nenhum evento encontrado no histórico para a data {data_evento}.")
    exit()

# =====================================================================
# 4. EXECUÇÃO DA CHECAGEM FINANCEIRA
# =====================================================================
resultado = checagem_valores(
    amort_ord_per=amort_ord_per,
    amex_per=amex_per,
    juros_per=juros_per,
    incorp_per=incorp_per,
    linha=dados_evento
)

# =====================================================================
# 5. EXIBIÇÃO DO RELATÓRIO ESTRUTURADO (COM ALTA PRECISÃO DECIMAL)
# =====================================================================
print("\n" + "=" * 68)
print(f"            RESULTADO DA REVISÃO - {data_evento}            ")
print("=" * 68)
print(f"STATUS DO EVENTO: {resultado['status']}")
print(f"MENSAGEM        : {resultado['msg']}")
print("-" * 68)
print("INDICADORES CALCULADOS:")
# 8 casas decimais para valores monetários / PU
print(f"  • Valor dos Juros (Site)      : R$ {resultado['juros_calculados']:,.8f}")
# 10 casas decimais para taxas e percentuais
print(f"  • Amortização Total Real (%)  :    {resultado['amort_total_real']:.10f}%")
print(f"  • Amortização Total Esp. (%)  :    {resultado['amort_total_esperada']:.10f}%")
print(f"  • Incorporação Real (%)       :    {resultado['incorp_real']:.10f}%")
print(f"  • Incorporação Esperada (%)   :    {resultado['incorp_esperada']:.10f}%")
print("=" * 68)