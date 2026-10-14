
import os
import logging
from typing import List, Literal

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("moliya_pro")

# FastAPI ilovasi
app = FastAPI(
    title="Moliya Pro 2.0 AI API",
    version="1.0.0",
)

# Flutter ilovasidan so'rovlarni qabul qilish
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Groq sozlamalari
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b",
)


# So'rov modellari
class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: List[ChatMessage] = Field(
        default_factory=list,
        max_length=12,
    )


class ChatResponse(BaseModel):
    reply: str


# Asosiy sahifa
@app.get("/")
def home():
    return {
        "app": "Moliya Pro 2.0 AI API",
        "status": "running",
    }


# Server holatini tekshirish
@app.get("/health")
def health():
    return {"status": "ok"}


# AI chat
@app.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    api_key = os.getenv("GROQ_API")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="Server sozlamasida GROQ_API topilmadi.",
        )

    messages = [
        {
            "role": "system",
            "content": (
                "Sen Moliya Pro 2.0 ilovasining o'zbek tilida "
                "javob beradigan AI yordamchisisan. Daromad, "
                "xarajat, shaxsiy byudjet, jamg'arma va moliyaviy "
                "rejalashtirish haqida tushunarli, amaliy va "
                "ehtiyotkor maslahat ber. Foydalanuvchi bermagan "
                "ma'lumotlarni o'ylab topma. Javoblarni ixcham, "
                "do'stona va o'zbek tilida yoz."
            ),
        }
    ]

    # Oldingi suhbat xabarlarini qo'shish
    for item in body.history:
        messages.append(
            {
                "role": item.role,
                "content": item.content,
            }
        )

    # Joriy xabar
    messages.append(
        {
            "role": "user",
            "content": body.message,
        }
    )

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
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        if response.status_code >= 400:
            # Javob matnini logga yozamiz, maxfiy kalitni emas.
            logger.error(
                "Groq API error: HTTP %s; response: %s",
                response.status_code,
                response.text[:1000],
            )

            raise HTTPException(
                status_code=502,
                detail=(
                    f"Groq API xatoligi (HTTP "
                    f"{response.status_code}). "
                    "Render server loglarini tekshiring."
                ),
            )

        data = response.json()
        reply = data["choices"][0]["message"]["content"].strip()

        return ChatResponse(
            reply=reply
            or "Hozir javob tayyorlay olmadim. Qayta urinib ko'r."
        )

    except HTTPException:
        raise

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="AI javobi kechikdi. Qayta urinib ko'r.",
        )

    except httpx.HTTPError:
        logger.exception("Groq bilan ulanishda HTTP xatosi")

        raise HTTPException(
            status_code=502,
            detail="AI xizmatiga ulanishda xatolik yuz berdi.",
        )

    except (KeyError, IndexError, ValueError):
        logger.exception("Groq javobini o'qishda xatolik")

        raise HTTPException(
            status_code=502,
            detail="AI javobini qayta ishlashda xatolik yuz berdi.",
        )
