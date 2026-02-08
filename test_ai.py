import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

print("🔍 Cerco i modelli disponibili per la tua chiave...")

try:
    trovato = False
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ Trovato: {m.name}")
            trovato = True
    
    if not trovato:
        print("⚠️ Nessun modello trovato. Controlla la chiave API.")

except Exception as e:
    print(f"❌ Errore: {e}")