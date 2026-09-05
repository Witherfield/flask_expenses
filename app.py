import sqlite3
from flask import Flask, redirect, render_template, request

app = Flask(__name__)


def get_db_connection():
    """
    Opens a connection to wydatki.db.
    row_factory` lets us access columns by name (row["TYP"]) 
    instead of only by position (row[1]) - much easier to read in templates.
    """
    connection = sqlite3.connect("wydatki.db")
    connection.row_factory = sqlite3.Row
    return connection


@app.route("/")
def home():
    return render_template("index.html")


DOZWOLONE_TYPY = ["KONTO", "GOTÓWKA", "PORTFEL", "PAYPAL", "CŁO"]

@app.route("/salda_faktyczne")
def salda_faktyczne():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT TYP, KWOTA FROM salda")
    rows = cursor.fetchall()
    connection.close()

    salda_dict = {row["TYP"]: row["KWOTA"] for row in rows}

    return render_template("salda_faktyczne.html", salda=rows,
                            typy=DOZWOLONE_TYPY, salda_dict=salda_dict,
                            active="salda_faktyczne")


@app.route("/salda_faktyczne/aktualizuj", methods=["POST"])
def aktualizuj_salda():
    connection = get_db_connection()
    cursor = connection.cursor()
    for typ, kwota in request.form.items():
        cursor.execute("INSERT OR REPLACE INTO salda (TYP, KWOTA) VALUES (?, ?)", (typ, float(kwota)))
    connection.commit()
    connection.close()
    return redirect("/salda_faktyczne")


@app.route("/transakcje")
def transakcje():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM transakcje WHERE DATA >= '2017-01-01' ORDER BY DATA DESC, ID DESC")
    rows = cursor.fetchall()
    connection.close()

    return render_template("transakcje.html", transakcje=rows, active="transakcje")


TYP_ORDER_G = ["BALANS", "PRZYCHÓD STAŁY", "WYDATEK STAŁY", "WYDATEK BIEŻĄCY", "PRZYCHÓD BIEŻĄCY", "TRANSFER"]  # <-- edit this list to reorder rows; put your actual TYP values here

TYP_ORDER_S = ["TRANSFER", "PRZYCHÓD BIEŻĄCY", "WYDATEK BIEŻĄCY"]  # <-- edit this list to reorder rows; put your actual TYP values here

@app.route("/transakcje_roczne")
def transakcje_roczne():
    connection = get_db_connection()
    cursor = connection.cursor()

    # --- Table 1: all accounts ---
    cursor.execute("""
        SELECT TYP, strftime('%Y', DATA) as ROK, SUM(KWOTA) as SUMA
        FROM transakcje
        WHERE DATA >= '2017-01-01' AND KONTO = 'GŁÓWNE'
        GROUP BY TYP, ROK
        ORDER BY ROK
    """)
    rows = cursor.fetchall()

    # --- Table 2: SKARBONKA only ---
    cursor.execute("""
        SELECT TYP, strftime('%Y', DATA) as ROK, SUM(KWOTA) as SUMA
        FROM transakcje
        WHERE DATA >= '2017-01-01' AND KONTO = 'SKARBONKA'
        GROUP BY TYP, ROK
        ORDER BY ROK
    """)
    rows_skarbonka = cursor.fetchall()

    connection.close()

    years = sorted(set(r["ROK"] for r in rows) | set(r["ROK"] for r in rows_skarbonka))

    def build_pivot(data_rows, order_list):
        pivot = {}
        for r in data_rows:
            pivot.setdefault(r["TYP"], {})[r["ROK"]] = r["SUMA"]

        ordered_typy = [t for t in order_list if t in pivot] + [t for t in pivot if t not in order_list]

        table_rows = []
        for typ in ordered_typy:
            year_vals = pivot[typ]
            table_rows.append({
                "TYP": typ,
                "values": [year_vals.get(y, 0) for y in years]
            })

        year_totals = [sum(row["values"][i] for row in table_rows) for i in range(len(years))]
        return table_rows, year_totals

    table_rows, year_totals = build_pivot(rows, TYP_ORDER_G)
    table_rows_skarbonka, year_totals_skarbonka = build_pivot(rows_skarbonka, TYP_ORDER_S)

    return render_template("transakcje_roczne.html",
                            years=years,
                            table_rows=table_rows, year_totals=year_totals,
                            table_rows_skarbonka=table_rows_skarbonka, year_totals_skarbonka=year_totals_skarbonka,
                            active="transakcje_roczne")


if __name__ == "__main__":
    app.run(debug=True)
