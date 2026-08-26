import sqlite3

DOZWOLONE_TYPY = ["KONTO",
                  "GOTÓWKA",
                  "PORTFEL",
                  "PAYPAL/CŁO"
                  ]

def add_saldo(typ: str, kwota: float) -> None:

    if typ not in DOZWOLONE_TYPY:
        raise ValueError(f"NIEPRAWIDŁOWY TYP: {typ}")
    
    connection = sqlite3.connect("wydatki.db")
    cursor = connection.cursor()
    cursor.execute("INSERT OR REPLACE INTO salda (TYP, KWOTA) VALUES (?, ?)", (typ, kwota))
    connection.commit()
    connection.close()

dane = [
    ("KONTO",   57368.85),
    ("GOTÓWKA",   920.00),
    ("PORTFEL",   962.28),
    ("PAYPAL/CŁO", 13.50)
    ]

for typ, kwota in dane:
    add_saldo(typ, kwota)
