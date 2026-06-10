from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import sqlite3
import io
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel

app = FastAPI()

DB_NAME = "konten.db"

# ================= DB =================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS konto (
            nutzer TEXT PRIMARY KEY,
            passwort TEXT,
            punkte INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ================= MODEL =================
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# ================= SCHEMAS =================
class User(BaseModel):
    username: str
    password: str

# ================= ROOT =================
@app.get("/")
def root():
    return {"status": "API läuft"}
