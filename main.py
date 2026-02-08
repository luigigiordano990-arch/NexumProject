import os
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Caricamento variabili
load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Configurazione Google Gemini AI
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
ai_model = genai.GenerativeModel('gemini-pro')

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELLI ---
class ProfessionistaCreate(BaseModel):
    nome: str
    cognome: str
    email: str
    password: str
    titolo_professionale: Optional[str] = ""
    descrizione: Optional[str] = ""
    immagine_profilo: Optional[str] = ""
    immagine_copertina: Optional[str] = ""

class PostCreate(BaseModel):
    autore: str
    contenuto: str

class MessaggioP2P(BaseModel):
    mittente: str
    destinatario: str
    testo: str
    file_data: Optional[str] = None
    file_name: Optional[str] = None

class ChatRequest(BaseModel):
    messaggio: str

class CommentoCreate(BaseModel):
    post_id: int
    autore: str
    testo: str

# --- ENDPOINT DI BENVENUTO ---
@app.get("/")
def read_root():
    return {"status": "online", "project": "Nexum API Professional"}

# --- REGISTRAZIONE E LOGIN ---
@app.post("/registrazione")
async def registrazione(prof: ProfessionistaCreate):
    try:
        data = prof.dict()
        response = supabase.table("professionisti").insert(data).execute()
        return {"status": "success", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
async def login(credenziali: dict):
    email = credenziali.get("email")
    password = credenziali.get("password")
    response = supabase.table("professionisti").select("*").eq("email", email).eq("password", password).execute()
    if not response.data:
        raise HTTPException(status_code=401, detail="Credenziali errate")
    return response.data[0]

# --- POSTS E COMMENTI ---
@app.get("/posts")
def get_posts():
    try:
        res = supabase.table("posts").select("*").order("created_at", desc=True).execute()
        return res.data if res.data else []
    except Exception:
        return []

@app.post("/posts/crea")
def crea_post(post: PostCreate):
    data = {"autore": post.autore, "contenuto": post.contenuto, "data": datetime.now().strftime("%d/%m/%Y")}
    return supabase.table("posts").insert(data).execute().data

@app.get("/posts/{post_id}/commenti")
def get_commenti(post_id: int):
    try:
        res = supabase.table("commenti").select("*").eq("post_id", post_id).order("created_at").execute()
        return res.data if res.data else []
    except Exception:
        return []

@app.post("/commenti/crea")
def crea_commento(comm: CommentoCreate):
    data = comm.dict()
    return supabase.table("commenti").insert(data).execute().data

# --- MESSAGGI ---
@app.get("/messaggi/conversazioni/{utente}")
def get_conv(utente: str):
    res = supabase.table("messaggi").select("mittente, destinatario").or_(f"mittente.eq.{utente},destinatario.eq.{utente}").execute()
    nomi = {m['mittente'] for m in res.data if m['mittente'] != utente} | {m['destinatario'] for m in res.data if m['destinatario'] != utente}
    return list(nomi)

@app.get("/messaggi/leggi/{u1}/{u2}")
def leggi(u1: str, u2: str):
    res = supabase.table("messaggi").select("*").or_(f"and(mittente.eq.{u1},destinatario.eq.{u2}),and(mittente.eq.{u2},destinatario.eq.{u1})").order("created_at").execute()
    return res.data

@app.post("/messaggi/invia")
def invia(msg: MessaggioP2P):
    data = msg.dict()
    data["timestamp"] = datetime.now().strftime("%H:%M")
    return supabase.table("messaggi").insert(data).execute().data

# --- NOTIFICHE ---
@app.get("/notifiche/{utente}")
def get_notifiche(utente: str):
    try:
        res = supabase.table("notifiche").select("*").eq("destinatario", utente).order("created_at", desc=True).execute()
        return res.data if res.data else []
    except Exception:
        return []

# --- ASSISTENTE AI ---
@app.post("/ai/chat")
async def chat_ai(req: ChatRequest):
    try:
        prompt = f"Sei l'assistente legale AI di Nexum. Rispondi in modo professionale e conciso: {req.messaggio}"
        response = ai_model.generate_content(prompt)
        return {"risposta": response.text}
    except Exception as e:
        return {"risposta": "Servizio AI momentaneamente non disponibile."}

# --- NEWS ---
@app.get("/news")
def get_news():
    return [{"id": 1, "titolo": "Nexum Fase Pro", "categoria": "Update", "riassunto": "AI e Notifiche attive.", "data": "Oggi"}]

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
