import os
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# 1. Caricamento variabili e Database
load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# 2. Configurazione AI (Sbloccata per termini professionali)
api_key_ai = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key_ai)

# CONFIGURAZIONE SBLOCCATA:
ai_model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    safety_settings=[
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
)

app = FastAPI()

# 3. Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELLI DATI ---

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
    testo: str  # Allineato perfettamente al tuo popup frontend

class CommentoCreate(BaseModel):
    post_id: int
    autore: str
    testo: str

# --- ENDPOINTS ---

@app.get("/")
def home():
    return {"status": "online", "message": "Nexum API Professional v3.0 Live"}

# --- REGISTRAZIONE & LOGIN ---
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
    data = {
        "autore": post.autore, 
        "contenuto": post.contenuto, 
        "data": datetime.now().strftime("%d/%m/%Y")
    }
    return supabase.table("posts").insert(data).execute().data

@app.get("/posts/{post_id}/commenti")
def get_commenti(post_id: int):
    try:
        res = supabase.table("commenti").select("*").eq("post_id", post_id).order("created_at").execute()
        return res.data if res.data else []
    except Exception:
        return []

# --- MESSAGGI ---
@app.get("/messaggi/conversazioni/{utente}")
def get_conv(utente: str):
    try:
        res = supabase.table("messaggi").select("mittente, destinatario").or_(f"mittente.eq.{utente},destinatario.eq.{utente}").execute()
        nomi = {m['mittente'] for m in res.data if m['mittente'] != utente} | {m['destinatario'] for m in res.data if m['destinatario'] != utente}
        return list(nomi)
    except Exception:
        return []

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

# --- ASSISTENTE AI (RISOLUTIVO PER L'ERRORE 'OCCUPATO') ---
@app.post("/chat")
async def chat_ai(req: ChatRequest):
    try:
        # Aggiungiamo istruzioni chiare per il modello
        prompt = f"Rispondi come un consulente legale esperto di Nexum alla seguente domanda: {req.testo}"
        # model.generate_content restituisce l'attributo .text se la generazione ha successo
        response = ai_model.generate_content(prompt)
        
        if response and response.text:
            return {"risposta": response.text}
        else:
            return {"risposta": "L'IA ha generato una risposta vuota. Riprova tra poco."}
            
    except Exception as e:
        print(f"Dettaglio Errore AI: {str(e)}")
        # Se l'errore riguarda la sicurezza (safety settings), Gemini blocca la risposta
        return {"risposta": "Spiacente, la richiesta è stata rifiutata per motivi di sicurezza o limite di quota."}

# --- NEWS ---
@app.get("/news")
def get_news():
    return [{"id": 1, "titolo": "Sistemi Operativi", "categoria": "Update", "riassunto": "Tutte le funzioni Pro sono live.", "data": "Oggi"}]

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)

