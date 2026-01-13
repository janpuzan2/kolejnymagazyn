import psycopg2
from psycopg2.extras import RealDictCursor

def connect_db():
    return psycopg2.connect(
        host="localhost",
        database="twoja_baza",
        user="twoj_uzytkownik",
        password="twoje_haslo"
    )

def add_kategoria(nazwa, opis):
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO kategorie (nazwa, opis) VALUES (%s, %s)", (nazwa, opis))
            conn.commit()

def delete_kategoria(kategoria_id):
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM kategorie WHERE id = %s", (kategoria_id,))
            conn.commit()

def add_produkt(nazwa, opis, kategoria_id):
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO produkty (nazwa, opis, kategoria_id) VALUES (%s, %s, %s)", (nazwa, opis, kategoria_id))
            conn.commit()

def delete_produkt(produkt_id):
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM produkty WHERE id = %s", (produkt_id,))
            conn.commit()

def get_kategorie():
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM kategorie")
            return cur.fetchall()

def get_produkty():
    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM produkty")
            return cur.fetchall()
