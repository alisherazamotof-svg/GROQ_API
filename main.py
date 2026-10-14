import os
from typing import List, Literal

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Moliya Pro 2.0 AI API", version="1.0.0")

# Mobile apps may call this API from different origins. Keep the API key on this server only.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: List[ChatMessage] = Field(default_factory=list, max_length=12)

class ChatResponse(BaseModel):
    reply: str

@app.get("/")
def home():
    return {"app": "Moliya Pro 2.0 AI API", "status": "running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    api_key = os.getenv("GROQ_API")
    if not api_key:
        raise HTTPException(status_code=500, detail="Server sozlamasida GROQ_API topilmadi.")

    messages = [{
        "role": "system",
        "content": (
            "Sen Moliya Pro 2.0 ilovasining o'zbek tilida javob beradigan AI yordamchisisan. "
            "Shaxsiy byudjet, daromad, xarajat, jamg'arma va moliyaviy rejalashtirish haqida "
            "tushunarli, amaliy va ehtiyotkor maslahat ber. Foydalanuvchi bermagan moliyaviy "
            "ma'lumotlarni o'ylab topma. Javoblarni ixcham va do'stona yoz. Bu umumiy ma'lumot, "
            "kafolatlangan moliyaviy maslahat emas."
        ),
    }]
    for item in body.history:
        messages.append({"role": item.role, "content": item.content})
    messages.append({"role": "user", "content": body.message})

    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 700,
    }
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(
                GROQ_URL,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
            )
       
if response.status_code >= 400:
    # Kalitni emas, faqat Groq qaytargan xato tafsilotini logga yozamiz.
    print(
        f"Groq API error: HTTP {response.status_code}; "
        f"response: {response.text[:1000]}"
    )
    raise HTTPException(
        status_code=502,
        detail=f"Groq API xatoligi (HTTP {response.status_code}). "
               "Batafsil ma'lumot server logida."
    )=504, detail="AI javobi kechikdi. Qayta urinib ko'r.")
    except (httpx.HTTPError, KeyError, IndexError, ValueError):
        raise HTTPException(status_code=502, detail="AI xizmatiga ulanishda xatolik yuz berdi.")
