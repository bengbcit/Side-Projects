import os
import sys
import json
import discord
import aiohttp
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".env"))
sys.stdout.reconfigure(line_buffering=True)

TOKEN = os.getenv("DISCORD_TOKEN").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY").strip()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY").strip()

print(f"[INIT] GEMINI    : {GEMINI_API_KEY[:5]}...")
print(f"[INIT] GROQ      : {GROQ_API_KEY[:5]}...")
print(f"[INIT] DEEPSEEK  : {DEEPSEEK_API_KEY[:5]}...")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


async def ask_gemini(session, text):
    payload = {"contents": [{"role": "user", "parts": [{"text": text}]}]}
    for model in ["gemini-2.5-flash", "gemini-1.5-pro"]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        async with session.post(url, json=payload) as resp:
            raw = await resp.text()
            if resp.status != 200:
                print(f"[Gemini/{model}] HTTP {resp.status}: {raw}")
                continue
            print(f"[Gemini/{model}] OK")
            return json.loads(raw)["candidates"][0]["content"]["parts"][0]["text"]
    raise Exception("All Gemini models failed")


async def ask_groq(session, text):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}",
               "Content-Type": "application/json"}
    async with session.post(url, headers=headers, json={"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": text}]}) as resp:
        raw = await resp.text()
        if resp.status != 200:
            print(f"[Groq] HTTP {resp.status}: {raw}")
            raise Exception(f"HTTP {resp.status}")
        return json.loads(raw)["choices"][0]["message"]["content"]


async def ask_deepseek(session, text):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}",
               "Content-Type": "application/json"}
    async with session.post(url, headers=headers, json={"model": "deepseek-chat", "messages": [{"role": "user", "content": text}]}) as resp:
        raw = await resp.text()
        if resp.status != 200:
            print(f"[DeepSeek] HTTP {resp.status}: {raw}")
            raise Exception(f"HTTP {resp.status}")
        return json.loads(raw)["choices"][0]["message"]["content"]


async def get_reply(text):
    async with aiohttp.ClientSession() as session:
        for name, fn in [("Gemini", ask_gemini), ("Groq", ask_groq), ("DeepSeek", ask_deepseek)]:
            try:
                reply = await fn(session, text)
                print(f"[{name}] OK")
                return f"[{name}] {reply}"
            except Exception as e:
                print(f"[{name}] FAILED: {e} — trying next...")
    return "All AI services failed — check the terminal for errors."


@client.event
async def on_ready():
    print(f"[READY] Logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith("!"):
        if message.content.startswith("!help"):
            await message.channel.send("Send any message → AI replies (Gemini → Groq → DeepSeek fallback)")
        return

    print(f"[MSG] {message.author}: {message.content}")
    async with message.channel.typing():
        reply = await get_reply(message.content)
    for chunk in [reply[i:i+1999] for i in range(0, len(reply), 1999)]:
        await message.channel.send(chunk)


client.run(TOKEN)
