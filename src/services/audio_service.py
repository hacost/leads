import os
from openai import AsyncOpenAI

async def transcribir_audio(audio_path: str) -> str:
    """
    Recibe la ruta física de un archivo de audio temporal y devuelve el texto transcrito
    usando el hardware rápido y gratuito de Groq (modelo Whisper).
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("No se encontró GROQ_API_KEY en el archivo .env. Por favor, crea una en console.groq.com")

    client = AsyncOpenAI(
        api_key=groq_api_key,
        base_url="https://api.groq.com/openai/v1"
    )
    
    with open(audio_path, "rb") as audio_file_obj:
        transcription = await client.audio.transcriptions.create(
            model="whisper-large-v3", 
            file=audio_file_obj
        )
        
    return transcription.text
