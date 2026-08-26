import sqlite3
from flask import Flask, render_template

app = Flask(__name__)


def get_db_connection():
    """
    Opens a connection to expenses.db.
    row_factory lets us access columns by name (row["TYP"]) instead of
    only by position (row[1]) - much easier to read in templates.
    """
    connection = sqlite3.connect("wydatki.db")
    connection.row_factory = sqlite3.Row
    return connection


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/salda")
def salda():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT TYP, KWOTA FROM salda")
    rows = cursor.fetchall() # list of all rows from the table
    connection.close()

    # Pass the rows into the template as a variable called "salda"
    return render_template("salda.html", salda=rows)


if __name__ == "__main__":
    app.run(debug=True)
