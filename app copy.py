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
TYP_ORDER_KARTA = ["PRZYCHÓD STAŁY", "WYDATEK BIEŻĄCY", "PRZYCHÓD BIEŻĄCY"]        # <-- edit as needed
TYP_ORDER_KAFETERYJNE = ["PRZYCHÓD STAŁY", "WYDATEK BIEŻĄCY"] # <-- edit as needed
TYP_ORDER_BONUSOWE = ['PRZYCHÓD STAŁY', 'WYDATEK BIEŻĄCY']    # <-- edit as needed
KONTO_ORDER = ["GŁÓWNE", "SKARBONKA", "KARTA PRZEDPŁACONA", "PUNKTY KAFETERYJNE", "PUNKTY BONUSOWE"]

NAVY_START_DATE = '2017-01-01'      # <-- always stays 2017, never changes
YEAR_FILTER_START = '2017-01-01'    # <-- bump this each year (e.g. to '2018-01-01') to drop old years from the rest

@app.route("/transakcje_roczne")
def transakcje_roczne():
    connection = get_db_connection()
    cursor = connection.cursor()

    def fetch(konto_value, start_date):
        cursor.execute("""
            SELECT TYP, strftime('%Y', DATA) as ROK, SUM(KWOTA) as SUMA
            FROM transakcje
            WHERE DATA >= ? AND KONTO = ?
            GROUP BY TYP, ROK
            ORDER BY ROK
        """, (start_date, konto_value))
        return cursor.fetchall()

    rows_glowne = fetch("GŁÓWNE", YEAR_FILTER_START)
    rows_skarbonka = fetch("SKARBONKA", YEAR_FILTER_START)
    rows_karta = fetch("KARTA PRZEDPŁACONA", YEAR_FILTER_START)
    rows_kafeteryjne = fetch("PUNKTY KAFETERYJNE", YEAR_FILTER_START)
    rows_bonusowe = fetch("PUNKTY BONUSOWE", YEAR_FILTER_START)

    # blue PODSUMOWANIE (with years) — follows the same adjustable filter as everything else
    cursor.execute("""
        SELECT KONTO, strftime('%Y', DATA) as ROK, SUM(KWOTA) as SUMA
        FROM transakcje
        WHERE KONTO <> 'NIEODEBRANE' AND DATA >= ?
        GROUP BY KONTO, ROK
        ORDER BY ROK
    """, (YEAR_FILTER_START,))
    rows_podsumowanie = cursor.fetchall()

    # navy PODSUMOWANIE (totals only, no years) — always fixed at 2017, ignores YEAR_FILTER_START
    cursor.execute("""
        SELECT KONTO, SUM(KWOTA) as SUMA
        FROM transakcje
        WHERE KONTO <> 'NIEODEBRANE' AND DATA >= ?
        GROUP BY KONTO
    """, (NAVY_START_DATE,))
    rows_navy = cursor.fetchall()

    connection.close()

    all_rows = [rows_glowne, rows_skarbonka, rows_karta, rows_kafeteryjne, rows_bonusowe, rows_podsumowanie]
    years = sorted(set(r["ROK"] for group in all_rows for r in group))


    def clean_zero(val):
        """Round to 2 decimals and eliminate -0.00 caused by floating point noise."""
        rounded = round(val, 2)
        return 0.0 if rounded == 0 else rounded


    def build_pivot(data_rows, order_list, key_field):
        pivot = {}
        for r in data_rows:
            pivot.setdefault(r[key_field], {})[r["ROK"]] = r["SUMA"]

        ordered_keys = [k for k in order_list if k in pivot] + [k for k in pivot if k not in order_list]

        table_rows = []
        for key in ordered_keys:
            year_vals = pivot[key]
            table_rows.append({
                key_field: key,
                "values": [clean_zero(year_vals.get(y, 0)) for y in years]
            })

        year_totals = [clean_zero(sum(row["values"][i] for row in table_rows)) for i in range(len(years))]
        return table_rows, year_totals

    table_rows, year_totals = build_pivot(rows_glowne, TYP_ORDER_G, "TYP")
    table_rows_skarbonka, year_totals_skarbonka = build_pivot(rows_skarbonka, TYP_ORDER_S, "TYP")
    table_rows_karta, year_totals_karta = build_pivot(rows_karta, TYP_ORDER_KARTA, "TYP")
    table_rows_kafeteryjne, year_totals_kafeteryjne = build_pivot(rows_kafeteryjne, TYP_ORDER_KAFETERYJNE, "TYP")
    table_rows_bonusowe, year_totals_bonusowe = build_pivot(rows_bonusowe, TYP_ORDER_BONUSOWE, "TYP")
    table_rows_podsumowanie, year_totals_podsumowanie = build_pivot(rows_podsumowanie, KONTO_ORDER, "KONTO")

    return render_template("transakcje_roczne.html",
                            years=years,
                            table_rows=table_rows, year_totals=year_totals,
                            table_rows_skarbonka=table_rows_skarbonka, year_totals_skarbonka=year_totals_skarbonka,
                            table_rows_karta=table_rows_karta, year_totals_karta=year_totals_karta,
                            table_rows_kafeteryjne=table_rows_kafeteryjne, year_totals_kafeteryjne=year_totals_kafeteryjne,
                            table_rows_bonusowe=table_rows_bonusowe, year_totals_bonusowe=year_totals_bonusowe,
                            table_rows_podsumowanie=table_rows_podsumowanie, year_totals_podsumowanie=year_totals_podsumowanie,
                            active="transakcje_roczne")


if __name__ == "__main__":
    app.run(debug=True)
