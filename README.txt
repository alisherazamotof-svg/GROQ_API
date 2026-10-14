MOLIYA PRO 2.0 — GROQ AI BACKEND

Pella Web App uchun fayllar:
- main.py
- requirements.txt

Environment Variables:
GROQ_API = Groq'dan olingan maxfiy API kaliti

Ishga tushirish komandasi (agar Pella so'rasa):
uvicorn main:app --host 0.0.0.0 --port $PORT

Tekshirish:
GET /health
POST /chat
JSON body: {"message":"Bugungi xarajatlarimni qanday rejalashtiray?"}

Muhim:
- GROQ_API kalitini Flutter main.dart ichiga yozmang.
- Pella loyiha sozlamasida environment variable sifatida saqlang.
- Server ishga tushgach, uning public URL manzilini saqlab qo'ying.
