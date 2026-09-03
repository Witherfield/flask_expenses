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


@app.route("/salda_faktyczne")
def salda_faktyczne():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT TYP, KWOTA FROM salda")
    rows = cursor.fetchall() # LIST OF ALL ROWS FROM THE TABLE
    connection.close()

    # PASS THE ROWS INTO THE TEMPLATE AS A VARIABLE CALLED "SALDA"
    return render_template("salda_faktyczne.html", salda=rows, active="salda")


@app.route("/salda_faktyczne/aktualizuj", methods=["POST"])
def aktualizuj_salda():
    connection = get_db_connection()
    cursor = connection.cursor()
    for typ, kwota in request.form.items():
        cursor.execute("INSERT OR REPLACE INTO salda (TYP, KWOTA) VALUES (?, ?)", (typ, float(kwota)))
    connection.commit()
    connection.close()
    return redirect("/salda_faktyczne")


if __name__ == "__main__":
    app.run(debug=True)
