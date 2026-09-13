def is_valid_luhn(card_number: str) -> bool:
    """Valida un número de tarjeta de crédito/débito usando el algoritmo de Luhn."""
    digits = [int(d) for d in card_number if d.isdigit()]
    if len(digits) < 13:
        return False

    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]

    total = sum(odd_digits)
    for d in even_digits:
        total += sum(divmod(d * 2, 10))

    return total % 10 == 0
