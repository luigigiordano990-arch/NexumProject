import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Carichiamo le chiavi dal file .env
load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELLI ---
class PostCreate(BaseModel):
    autore: str
    contenuto: str

class MessaggioP2P(BaseModel):
    mittente: str
    destinatario: str
    testo: str
    file_data: Optional[str] = None
    file_name: Optional[str] = None

# --- ENDPOINTS POST (SUPABASE) ---
@app.get("/posts")
def get_all_posts():
    response = supabase.table("posts").select("*").order("created_at", desc=True).execute()
    return response.data

@app.get("/posts/{autore}")
def get_user_posts(autore: str):
    response = supabase.table("posts").select("*").eq("autore", autore).order("created_at", desc=True).execute()
    return response.data

@app.post("/posts/crea")
def crea_post(post: PostCreate):
    data = {
        "autore": post.autore,
        "contenuto": post.contenuto,
        "data": datetime.now().strftime("%d/%m/%Y")
    }
    response = supabase.table("posts").insert(data).execute()
    return response.data

# --- ENDPOINTS MESSAGGI (SUPABASE) ---
@app.post("/messaggi/invia")
def invia_messaggio(msg: MessaggioP2P):
    data = {
        "mittente": msg.mittente,
        "destinatario": msg.destinatario,
        "testo": msg.testo,
        "timestamp": datetime.now().strftime("%H:%M"),
        "file_data": msg.file_data,
        "file_name": msg.file_name
    }
    response = supabase.table("messaggi").insert(data).execute()
    return response.data

@app.get("/messaggi/leggi/{u1}/{u2}")
def leggi_chat(u1: str, u2: str):
    # Query complessa: messaggi tra u1 e u2 OR tra u2 e u1
    response = supabase.table("messaggi").select("*").or_(f"and(mittente.eq.{u1},destinatario.eq.{u2}),and(mittente.eq.{u2},destinatario.eq.{u1})").order("created_at").execute()
    return response.data

# --- ALTRI ENDPOINTS (News rimangono statiche per ora) ---
@app.get("/news")
def get_news():
    return [{"id": 1, "titolo": "Nexum è Online!", "categoria": "Update", "riassunto": "Database collegato con successo.", "data": "Oggi"}]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)