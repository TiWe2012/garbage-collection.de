#alle koordinaten 2 mal /2
from time import sleep
from streamlit import *
import sqlite3
from PIL import Image, ImageTk
import os
import cv2
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

#Login
DB_NAME = "konten.db"
current_name = None
current_punkte = 0

#Framework einrichten
app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hallo FastAPI"}

# Tabelle erstellen
def init_db():
    # Funktion zum Prüfen ob die Datei eine echte SQLite-DB ist
    def is_valid_sqlite(path):
        if not os.path.exists(path):
            return False
        try:
            conn = sqlite3.connect(path)
            conn.execute("PRAGMA schema_version;")
            conn.close()
            return True
        except sqlite3.DatabaseError:
            return False

    # Wenn Datei beschädigt → löschen
    if not is_valid_sqlite(DB_NAME):
        print("⚠️ konten.db beschädigt → wird neu erstellt…")
        if os.path.exists(DB_NAME):
            os.remove(DB_NAME)

    # Jetzt NEUE Verbindung öffnen
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Tabelle erstellen
    cur.execute("""
        CREATE TABLE IF NOT EXISTS konto (
            nutzer TEXT PRIMARY KEY,
            passwort TEXT,
            kontostand REAL DEFAULT 0,
            punkte INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()

#Fenster zum Login
def start_gui():
    global current_name
    start = set_page_config(
    page_title="Login/Sign up",
    layout="wide"
)
    title("Login/Sign up")

    text("Login/Sign up")
    username_entry = text_input("Username")

    password_entry = text_input("Password")

    def login():
        global current_name
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT * FROM konto WHERE username_entry=? AND password_entry=?", (username_entry, password_entry))
        user = cur.fetchone()
        conn.close()
        if user:
            current_name = nutzer
            current_punkte = user[1]
            info(f"Willkommen, {nutzer}!")
            start.destroy()
        else:
            error("Benutzer oder Passwort falsch.")

    def register():
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        try:
            cur.execute("ALTER TABLE konto ADD COLUMN punkte INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        try:
            cur.execute("INSERT INTO konto (nutzer, passwort, kontostand, punkte) VALUES (?, ?, 0, 0)", (nutzer, pw))
            conn.commit()
            info("Registrierung erfolgreich! Du kannst dich jetzt einloggen.")
        except sqlite3.IntegrityError:
            error("Benutzername existiert bereits.")
        conn.close()
        
    if button("Login"):
        login()
        label = "Login"
    if button("Registrieren"):
        register()
        label = "registrieren"

#Login
if __name__ == "__main__":
    init_db()
    start_gui()

#Variablen
Name = current_name
Punktestand = current_punkte
cap = None       # Kameraobjekt
live_frame = None  # letztes Kamerabild
running = False    # Flag für Livebild

#Fenster öffnen
root = set_page_config(
    page_title="Login/Sign up",
    layout="wide"
)
title("Login/Sign up")

#Jahreszeit herausfinden
monat = datetime.now().month

#Hintergrund erstellen
if monat in [3, 4, 5]:
    Hintergrund = image("Fruehling.png")
elif monat in [6, 7, 8]:
    Hintergrund = image("Sommer.png")
elif monat in [9, 10, 11]:
    Hintergrund = image("Herbst.png")
elif monat in [12, 1, 2]:
    Hintergrund = image("Winter.png")


#Kontobefehl
def Konto():
    with expander("Konto"):
        Konto = text(text=f"""Name: {Name}
Punktestand: {Punktestand}""", tag="löschbar")

#Kontobutton
Kontobutton = Image.open("Konto.png").resize((45, 45), Image.LANCZOS)
with expander("Kontobutton"):
    image(Kontobutton, width=45)
    if button("Kontobutton"):
        Konto()

#Homebefehl
def alles_schließen():
    c.delete("löschbar")

#Homebutton
Homebutton = Image.open("Home.png").resize((45, 45), Image.LANCZOS)
with expander("Homebutton"):
    image(Homebutton, width=45)
    if button("Homebutton"):
        alles_schließen()
    
#Ranglistenbefehl
def rangliste_top10():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT nutzer, punkte FROM konto ORDER BY punkte DESC LIMIT 10")
    top10 = cur.fetchall()
    conn.close()
    
    rangliste_text = "🏆 Top 10 Spieler nach Punkten:\n"
    rangliste_text += "\n".join(f"{i+1}. {nutzer}: {punkte} Punkte" for i, (nutzer, punkte) in enumerate(top10))
    return rangliste_text

def rangliste_anzeigen():
    rangliste = rangliste_top10()
    with expander():
        ranglisten = text(rangliste, tag="löschbar")

        
#Ranglistenbutton
Ranglistenbutton = Image.open("Rangliste.png").resize((45, 45), Image.LANCZOS)
with expander("Ranglistenbutton"):
    image(Ranglistenbutton, width=45)
    if button("Ranglistenbutton"):
        rangliste_anzeigen()

#Bild-Analyse
def Bild_analysieren():
    Bildinput = "kamerabild.jpg"
    try:
        with Image.open(Bildinput) as img:
            print(f"Bild {Bildinput} geladen.")

    except FileNotFoundError:
        print("Ein Fehler ist aufgetreten")
        exit()

    if os.path.exists(Bildinput):
        os.remove(Bildinput)
        print(f"Datei {Bildinput} wurde erfolgreich gelöscht.")
    else:
        print("Die Datei existiert nicht.")

#Kamera-Befehl
def Kamera_öffnen():
    cap = cv2.VideoCapture(0)

    while True:
# Prüfen, ob die Kamera geöffnet werden konnte
        if not cap.isOpened():
            print("Kamera kann nicht geöffnet werden")
            exit()

#Kamera-Bild
        ret, frame = cap.read()

# Das Bild anzeigen
        cv2.imshow('Webcam Feed', frame)

# 'q' drücken, um zu beenden
        if cv2.waitKey(1) & 0xFF == ord('q'):
            if ret:
                cv2.imwrite('kamerabild.jpg', frame)
                print("Bild wurde als kamerabild.jpg gespeichert")
                break
    cv2.destroyAllWindows()
    Bild_analysieren()


#Kamerabutton
Kamerabutton = Image.open("Kamera.png").resize((45, 45), Image.LANCZOS)
with expander("Kamerabutton"):
    image(Kamerabutton, width=45)
    if button("Kamerabutton"):
        Kamera_öffnen()
