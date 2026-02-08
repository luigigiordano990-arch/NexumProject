import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Carichiamo le chiavi dal file .env (o dalle variabili d'ambiente di Render)
load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

app = FastAPI()

# Configurazione CORS per permettere a Vercel di parlare con Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELLI DATI (Pydantic) ---

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

# --- ENDPOINTS PROFESSIONISTI (REGISTRAZIONE E LOGIN) ---

@app.post("/registrazione")
def registrazione(prof: ProfessionistaCreate):
    try:
        data = {
            "nome": prof.nome,
            "cognome": prof.cognome,
            "email": prof.email,
            "password": prof.password, 
            "titolo_professionale": prof.titolo_professionale,
            "descrizione": prof.descrizione,
            "immagine_profilo": prof.immagine_profilo,
            "immagine_copertina": prof.immagine_copertina
        }
        response = supabase.table("professionisti").insert(data).execute()
        return response.data
    except Exception as e:
        print(f"Errore registrazione: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
def login(credenziali: dict):
    email = credenziali.get("email")
    password = credenziali.get("password")
    
    try:
        response = supabase.table("professionisti").select("*").eq("email", email).eq("password", password).execute()
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=401, detail="Email o password errati")
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ENDPOINTS POST ---

@app.get("/posts")
def get_all_posts():
    response = supabase.table("posts").select("*").order("created_at", desc=True).execute()
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

# --- ENDPOINTS MESSAGGI ---

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
    response = supabase.table("messaggi").select("*").or_(f"and(mittente.eq.{u1},destinatario.eq.{u2}),and(mittente.eq.{u2},destinatario.eq.{u1})").order("created_at").execute()
    return response.data

@app.get("/messaggi/conversazioni/{utente}")
def get_conversazioni(utente: str):
    # Recupera tutti i nomi delle persone con cui l'utente ha parlato
    res = supabase.table("messaggi").select("mittente, destinatario").or_(f"mittente.eq.{utente},destinatario.eq.{utente}").execute()
    nomi = set()
    for m in res.data:
        if m['mittente'] != utente: nomi.add(m['mittente'])
        if m['destinatario'] != utente: nomi.add(m['destinatario'])
    return list(nomi)

# --- HOME / TEST ---

@app.get("/")
def home():
    return {"status": "online", "message": "Nexum Backend API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
