import os
import json
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = FastAPI()

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar Gemini
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("No se encontró la variable GEMINI_API_KEY")

genai.configure(api_key=API_KEY)

class AnalysisRequest(BaseModel):
    image: str
    customPrompt: str = ""

@app.get("/")
def home():
    return {"status": "Sentinel AI Backend (Python) is running"}

@app.post("/analyze")
async def analyze_image(request: AnalysisRequest):
    try:
        # 1. Limpiar la imagen Base64
        if "," in request.image:
            clean_image_data = request.image.split(",")[1]
        else:
            clean_image_data = request.image

        # 2. Configurar el modelo (Mantenemos gemini-2.5-flash para velocidad)
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config={"response_mime_type": "application/json"}
        )

        # 3. Preparar el prompt MODIFICADO PARA DETECCIÓN HUMANA
        prompt = f"""
        Eres un sistema de vigilancia de alta seguridad. Tu objetivo principal es detectar la presencia de seres humanos.
        
        REGLA DE AMENAZA:
        - Si detectas a una persona, un hombre, una mujer, un niño, o cualquier cosa que se parezca a un ser humano o silueta humana, DEBES marcar "suspicious" como true.
        - La simple presencia de un humano en la imagen se considera una amenaza para este sistema.
        - Si NO observas ningún ser humano, marca "suspicious" como false.
        
        Contexto adicional solicitado: {request.customPrompt if request.customPrompt else "Ninguno"}
        
        Responde ÚNICAMENTE con JSON válido con esta estructura:
        {{
          "suspicious": boolean,
          "description": "Describe brevemente en español si ves humanos (hombres, mujeres, niños) y qué están haciendo. Si no ves humanos, indica que el área está despejada."
        }}
        """

        # 4. Enviar a Gemini
        response = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": clean_image_data}
        ])

        # 5. Parsear y devolver la respuesta
        result_json = json.loads(response.text)
        return result_json

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)