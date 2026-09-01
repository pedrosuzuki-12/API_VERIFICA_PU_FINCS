def num_br(valor):
    # converte "1.257,84135892" -> 1257.84135892
    # e trata None como 0.0
    if valor is None:
        return 0.0
    if isinstance(valor, (int,float)):
        return float(valor)

    try:
        texto=str(valor).replace(".","").replace(",",".").strip()
        return float(texto)
    except ValueError:
        return 0.0