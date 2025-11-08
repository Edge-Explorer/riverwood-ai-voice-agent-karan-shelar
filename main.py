import os
import requests
import subprocess
from dotenv import load_dotenv
from prompts import compose_prompt
import google.generativeai as genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID", "2EiwWnXFnvU5JabPnv8n")  # Clyde (free)
MEMORY_SIZE = int(os.getenv("MEMORY_SIZE", "3"))
OUTPUT_AUDIO = os.getenv("OUTPUT_AUDIO", "agent_reply.mp3")

def call_gemini(prompt: str, temperature: float = 0.2, max_tokens: int = 300):
    """Call Gemini 2.5 Pro and return text output (robust parsing)."""
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-pro")

        safety_settings = [
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUAL_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        response = model.generate_content(
            prompt,
            safety_settings=safety_settings,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )

        if hasattr(response, "text") and response.text:
            return response.text.strip()

        if hasattr(response, "candidates") and response.candidates:
            for c in response.candidates:
                if hasattr(c, "content") and getattr(c.content, "parts", None):
                    parts = c.content.parts
                    texts = [p.text for p in parts if hasattr(p, "text") and p.text]
                    if texts:
                        return " ".join(texts).strip()

        fallback_prompt = (
            "Please respond politely and briefly to this user message:\n" + prompt[-1000:]
        )
        response2 = model.generate_content(
            fallback_prompt,
            safety_settings=safety_settings,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )

        if hasattr(response2, "text") and response2.text:
            return response2.text.strip()

        return "Namaste! Main theek hoon — batayein, aapko kis cheez mein madad chahiye?"

    except Exception as e:
        print("Gemini error:", e)
        return "Maaf kijiye, mujhe thodi dikkat aa rahi hai. Kya aap apna sawaal dobara bata sakte hain?"

def eleven_tts(text: str, out_file: str = OUTPUT_AUDIO):
    """Convert text → speech using ElevenLabs API."""
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID}"
        headers = {
            "xi-api-key": ELEVEN_API_KEY,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",  # works for free tier
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }

        response = requests.post(url, headers=headers, json=payload, stream=True, timeout=60)
        print(f"TTS response → {response.status_code} | {response.headers.get('content-type')}")

        if "audio" not in response.headers.get("content-type", ""):
            print("TTS error details:", response.text)
            return None

        abs_path = os.path.abspath(out_file)
        with open(abs_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return abs_path
    except Exception as e:
        print("ElevenLabs TTS error:", e)
        return None

def play_audio(path):
    """Play audio via FFplay (FFmpeg required)."""
    try:
        abs_path = os.path.abspath(path)
        subprocess.run(
            ["ffplay", "-nodisp", "-autoexit", abs_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except Exception as e:
        print("Could not auto-play audio. Open", abs_path, "manually. Error:", e)

def main():
    print("Riverwood AI Voice Agent — prototype (text mode). Type 'exit' to quit.")
    memory = []

    greet = "Namaste Sir, chai pee li? Main Riverwood se bol raha hoon — kaise madad kar sakta hoon aaj?"
    print("Agent:", greet)

    audio_path = eleven_tts(greet, OUTPUT_AUDIO)
    if audio_path:
        play_audio(audio_path)

    while True:
        user_input = input("\nYou: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye — best of luck with the challenge!")
            break

        prompt = compose_prompt(user_input, memory)
        print("...calling Gemini Pro for response (this may take a sec)...")
        assistant_text = call_gemini(prompt)

        print("\nAgent (text):", assistant_text)

        audio_path = eleven_tts(assistant_text, OUTPUT_AUDIO)
        if audio_path:
            print(f"Audio saved to {OUTPUT_AUDIO} — playing...")
            play_audio(audio_path)
        else:
            print("TTS failed — skipping audio playback.")

        memory.append((user_input, assistant_text))
        if len(memory) > MEMORY_SIZE:
            memory = memory[-MEMORY_SIZE:]

if __name__ == "__main__":
    main()
