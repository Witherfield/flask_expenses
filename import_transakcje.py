import pandas as pd
import sqlite3

def import_transakcje(xlsx_path="ALL.xlsx", sheet="ALL", db_path="wydatki.db"):
    # cols A:F -> DATA, TYP, KATEGORIA, MIEJSCE, KWOTA, KONTO
    df = pd.read_excel(xlsx_path, sheet_name=sheet, usecols="A:F",
                        names=["DATA", "TYP", "KATEGORIA", "MIEJSCE", "KWOTA", "KONTO"],
                        header=0)

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    for _, row in df.iterrows():
        data_str = row["DATA"].strftime("%Y-%m-%d") if pd.notna(row["DATA"]) else None
        cursor.execute("""
            INSERT INTO transakcje (DATA, TYP, KATEGORIA, MIEJSCE, KWOTA, KONTO)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (data_str, row["TYP"], row["KATEGORIA"], row["MIEJSCE"], row["KWOTA"], row["KONTO"]))

    connection.commit()
    connection.close()
    print(f"Inserted {len(df)} rows.")

if __name__ == "__main__":
    import_transakcje()
    input("Press Enter to exit.")
