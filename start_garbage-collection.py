#alle koordinaten 2 mal /2
from time import sleep
from tkinter import *
from tkinter import messagebox
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
    start = Tk()
    start.title("Login / Registrierung")
    start.geometry("300x250")

    Label(start, text="Benutzername:").pack()
    username_entry = Entry(start)
    username_entry.pack()

    Label(start, text="Passwort:").pack()
    password_entry = Entry(start, show="*")
    password_entry.pack()

    def login():
        global current_name
        nutzer = username_entry.get()
        pw = password_entry.get()
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT * FROM konto WHERE nutzer=? AND passwort=?", (nutzer, pw))
        user = cur.fetchone()
        conn.close()
        if user:
            current_name = nutzer
            current_punkte = user[1]
            messagebox.showinfo("Erfolg", f"Willkommen, {nutzer}!")
            start.destroy()
        else:
            messagebox.showerror("Fehler", "Benutzer oder Passwort falsch.")

    def register():
        nutzer = username_entry.get()
        pw = password_entry.get()
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        try:
            cur.execute("ALTER TABLE konto ADD COLUMN punkte INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        try:
            cur.execute("INSERT INTO konto (nutzer, passwort, kontostand, punkte) VALUES (?, ?, 0, 0)", (nutzer, pw))
            conn.commit()
            messagebox.showinfo("Erfolg", "Registrierung erfolgreich! Du kannst dich jetzt einloggen.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Fehler", "Benutzername existiert bereits.")
        conn.close()
        
    Button(start, text="Login", command=login).pack(pady=5)
    Button(start, text="Registrieren", command=register).pack(pady=5)
    start.mainloop()

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
root = Tk()
root.title("Garbage Collection")

#Eine "Canva" erstellen
c = Canvas(root, height=1920, width=1080, bg="white")
c.pack()

#Jahreszeit herausfinden
monat = datetime.now().month

#Hintergrund erstellen
if monat in [3, 4, 5]:
    Hintergrund = Image.open("Fruehling.png")
elif monat in [6, 7, 8]:
    Hintergrund = Image.open("Sommer.png")
elif monat in [9, 10, 11]:
    Hintergrund = Image.open("Herbst.png")
elif monat in [12, 1, 2]:
    Hintergrund = Image.open("Winter.png")
verkleinereHintergrund = Hintergrund.resize((1080, 1920), Image.LANCZOS)
#optional !LÖSCHEN!
verkleinereHintergrund2 = verkleinereHintergrund.resize((270, 480), Image.LANCZOS)
#Vorbei
Hintergrund_Photo = ImageTk.PhotoImage(verkleinereHintergrund2) #die "2" löschen
c.create_image(135, 200, image=Hintergrund_Photo) #neue koordinaten 540, 920

#Kontobefehl
def Konto():
    Konto = Label(root, text=f"""Name: {Name}
Punktestand: {Punktestand}""")
    c.create_window(135, 240, window=Konto, tags="löschbar") #neue Koordinaten 540, 1000

#Kontobutton
Kontobutton = Image.open("Konto.png")
verkleinereKontobutton = Kontobutton.resize((45, 45), Image.LANCZOS) #Neue koordinaten 180, 180
Kontobutton_Photo = ImageTk.PhotoImage(verkleinereKontobutton)
kontobutton = Button(root, image=Kontobutton_Photo, command=Konto)
c.create_window(21, 411, window=kontobutton)#Neue koordinaten 90, 1830

#Homebefehl
def alles_schließen():
    c.delete("löschbar")

#Homebutton
Homebutton = Image.open("Home.png")
verkleinereHomebutton = Homebutton.resize((45, 45), Image.LANCZOS) #Neue koordinaten 180, 180
Homebutton_Photo = ImageTk.PhotoImage(verkleinereHomebutton)
homebutton = Button(root, image=Homebutton_Photo, command=alles_schließen)
c.create_window(247, 23, window=homebutton)#Neue koordinaten 990, 90

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
    ranglisten = Label(root, text=rangliste)
    c.create_window(135, 240, window=ranglisten, tags="löschbar") #neue Koordinaten 540, 1000
        
#Ranglistenbutton
Ranglistenbutton = Image.open("Rangliste.png")
verkleinereRanglistenbutton = Ranglistenbutton.resize((45, 45), Image.LANCZOS) #Neue Koordinaten 180, 180
Ranglistenbutton_Photo = ImageTk.PhotoImage(verkleinereRanglistenbutton)
ranglistenbutton = Button(root, image=Ranglistenbutton_Photo, command=rangliste_anzeigen)
c.create_window(112, 457, window=ranglistenbutton)#Neue Koordinaten 450, 1830

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
Kamerabutton = Image.open("Kamera.png")
verkleinereKamerabutton = Kamerabutton.resize((45, 45), Image.LANCZOS) #Neue Koordinaten 180, 180
Kamerabutton_Photo = ImageTk.PhotoImage(verkleinereKamerabutton)
kamerabutton = Button(root, image=Kamerabutton_Photo, command=Kamera_öffnen)
c.create_window(458, 158, window=kamerabutton) #Neue Koordinaten 1830, 630



#Die Schleife starten
root.mainloop()
