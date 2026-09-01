import requests

url = "https://services-ft.oliveiratrust.com.br/app/v1/titulos/historico_pu/41021?page=1&limit=10"

# Simulando um navegador real (Chrome no Windows/Linux)
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.oliveiratrust.com.br/",
    "Origin": "https://www.oliveiratrust.com.br",
    "Accept": "application/json, text/plain, */*",
}

def busca_historico(id_ot,data_evento):
    url=f"https://services-ft.oliveiratrust.com.br/app/v1/titulos/historico_pu/{id_ot}?page=1&limit=40"
    resposta=requests.get(url,headers=headers)

    if resposta.status_code != 200:
        print("Erro:", resposta.status_code)
        print(resposta.text)
        return None

    dados=resposta.json()
    infos=dados["data"]["data"]
    for item in infos:
        if item["data"]==data_evento:
            return (
                item["valor_nominal"],
                item["juros"],
                item["premio"],
                item["pu"],
                item["amort_pgto"],
                item["juros_pgto"],
                item["premio_pgto"],
                item["total_pgto"],
            )
    return None
        


resultado = busca_historico(62801, "2026-07-19")

if resultado:
    print(*resultado)
else:
    print("Data não encontrada.")