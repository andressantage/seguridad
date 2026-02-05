import os
import json
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

# Cargar variables de entorno (para desarrollo local)
load_dotenv()

app = FastAPI()

# Configuración de CORS (Permite que tu HTML se conecte al servidor)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, pon aquí la URL de tu frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar Gemini
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("No se encontró la variable GEMINI_API_KEY")

genai.configure(api_key=API_KEY)

# Modelo de datos que esperamos recibir del HTML
class AnalysisRequest(BaseModel):
    image: str
    customPrompt: str = ""

@app.get("/")
def home():
    return {"status": "Sentinel AI Backend (Python) is running"}

@app.post("/analyze")
async def analyze_image(request: AnalysisRequest):
    try:
        # 1. Limpiar la imagen Base64 (quitar el encabezado "data:image/jpeg;base64,")
        if "," in request.image:
            clean_image_data = request.image.split(",")[1]
        else:
            clean_image_data = request.image

        # 2. Configurar el modelo
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config={"response_mime_type": "application/json"}
        )

        # 3. Preparar el prompt
        prompt = f"""
        Actúa como sistema de vigilancia CCTV. Analiza esta imagen.
        Busca específicamente: personas forzando vehículos, robando autos, llantas, partes de vehiculos, cuchillos, armas o violencia.
        {f"Busca también específicamente: Si existe una persona ahi en la imagen o si vez un cuchillo si es asi suspicious deber ser true  {request.customPrompt}" if request.customPrompt else ""}
        
        Responde ÚNICAMENTE con JSON válido con esta estructura:
        {{
          "suspicious": boolean,
          "description": "breve descripción real de lo observado en español"
        }}
        """

        # 4. Enviar a Gemini (Texto + Imagen)
        response = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": clean_image_data}
        ])

        # 5. Parsear y devolver la respuesta
        # Gemini devuelve un string JSON, lo convertimos a dict de Python
        result_json = json.loads(response.text)
        return result_json

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Esto es para correrlo localmente, en Render se usa el comando de arranque

    uvicorn.run(app, host="0.0.0.0", port=8000)
