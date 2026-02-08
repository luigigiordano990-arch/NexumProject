from sqlalchemy import Column, Integer, String, Text, Boolean
from database import Base

# Tabella delle Notizie (già esistente)
class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    titolo = Column(String, index=True)
    categoria = Column(String) # Es: "Fisco", "Legale", "Generale"
    riassunto = Column(Text)

# NUOVA Tabella Utenti (Per la registrazione e il profilo pubblico)
class Utente(Base):
    __tablename__ = "utenti"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String) # In futuro la cripteremo
    nome = Column(String)
    cognome = Column(String)
    
    # Il campo più importante per la tua visione:
    titolo_professionale = Column(String) # Es: "Avvocato", "Commercialista", "Consulente"
    
    # Per il profilo pubblico
    descrizione = Column(Text, nullable=True) # "Sono specializzato in diritto penale..."
    sito_web = Column(String, nullable=True)
    profilo_pubblico_attivo = Column(Boolean, default=False)