from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ⚠️ SOSTITUISCI 'tuapassword' CON LA PASSWORD CHE HAI MESSO IN PGADMIN!
# La struttura è: postgresql://utente:password@indirizzo:porta/nome_db
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:lucia2006@localhost/nexum"

# Creiamo il motore di connessione
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Creiamo una "sessione" (un canale di comunicazione)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Questa è la classe base per i modelli (le tabelle)
Base = declarative_base()

# Funzione per prendere il database quando serve
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()