from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import sqlite3
import io
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel

app = FastAPI()

DB_NAME = "konten.db"

# =============================
# DATABASE
# =============================
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

# =============================
# MODEL
# =============================
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)

# =============================
# SCHEMAS
# =============================
class User(BaseModel):
    username: str
    password: str

# =============================
# ROOT
# =============================
@app.get("/")
def root():
    return {"status": "API läuft"}

# =============================
# REGISTER
# =============================
@app.post("/register")
def register(user: User):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO konto (nutzer, passwort) VALUES (?, ?)",
            (user.username, user.password),
        )
        conn.commit()
        return {"success": True}
    except:
        return {"success": False, "error": "User existiert bereits"}
    finally:
        conn.close()

# =============================
# LOGIN
# =============================
@app.post("/login")
def login(user: User):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "SELECT nutzer, punkte FROM konto WHERE nutzer=? AND passwort=?",
        (user.username, user.password),
    )

    data = cur.fetchone()
    conn.close()

    if data:
        return {
            "success": True,
            "user": data[0],
            "punkte": data[1]
        }

    return {"success": False}

# =============================
# LEADERBOARD
# =============================
@app.get("/leaderboard")
def leaderboard():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "SELECT nutzer, punkte FROM konto ORDER BY punkte DESC LIMIT 10"
    )

    data = cur.fetchall()
    conn.close()

    return {"top10": data}

# =============================
# IMAGE ANALYSIS (CLIP)
# =============================
@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    image = Image.open(io.BytesIO(await file.read())).convert("RGB")

    labels = ["trash", "clean", "recycling"]

    inputs = processor(
        text=labels,
        images=image,
        return_tensors="pt",
        padding=True
    )

    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)

    probs = outputs.logits_per_image.softmax(dim=-1)[0]

    idx = probs.argmax().item()

    return {
        "label": labels[idx],
        "confidence": float(probs[idx])
    }
