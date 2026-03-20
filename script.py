import os
import sys
import re
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from google import genai


def extract_video_id(input_str):
    patterns = [
        r'(?:youtube\.com/watch\?(?:.*&)?v=)([a-zA-Z0-9_-]{11})',
        r'(?:youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, input_str)
        if match:
            return match.group(1)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', input_str):
        return input_str
    return None


GEMINI_MODEL = "gemini-2.5-flash"


def call_gemini(api_key: str, prompt: str) -> str:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return response.text


def save_transcript(text: str, suffix: str = "") -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = os.path.join(script_dir, "transcripts")
    os.makedirs(target_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path = os.path.join(target_dir, f"{timestamp}{suffix}.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)
    return file_path


def main():
    # Usage: script.py <url> [apikey] [--prevod] [--kljucne]
    if len(sys.argv) < 2:
        print("Upotreba: python script.py <url> [apikey] [--prevod] [--kljucne]")
        sys.exit(1)

    url     = None
    api_key = None
    prevod  = False
    kljucne = False

    for arg in sys.argv[1:]:
        if arg == "--prevod":
            prevod = True
        elif arg == "--kljucne":
            kljucne = True
        elif url is None:
            url = arg
        else:
            api_key = arg

    if not url:
        print("❌ URL ili video ID nije naveden.")
        sys.exit(1)

    video_id = extract_video_id(url)
    if not video_id:
        print(f"❌ Nije moguće izvući video ID iz: {url}")
        sys.exit(1)

    print(f"🎬 Video ID: {video_id}")

    # Fetch transcript
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.fetch(video_id)
        formatter = TextFormatter()
        transcript_text = formatter.format_transcript(transcript_list)
    except Exception as e:
        print(f"❌ Greška pri preuzimanju transkripta: {e}")
        sys.exit(1)

    raw_path = save_transcript(transcript_text, suffix="_original")
    print(f"✅ Originalni transkript sačuvan: {raw_path}")

    needs_gemini = prevod or kljucne
    if needs_gemini:
        if not api_key:
            print("❌ Gemini API ključ je neophodan za prevod / ključne tačke.")
            sys.exit(1)

        if prevod:
            print("🌐 Prevodim na srpski…")
            try:
                prompt = (
                    "Prevedi sledeći YouTube transkript na srpski jezik. "
                    "Zadrži podele na pasuse. Ispiši samo prevedeni tekst, ništa drugo.\n\n"
                    f"{transcript_text}"
                )
                translated = call_gemini(api_key, prompt)
                t_path = save_transcript(translated, suffix="_srpski")
                print("\n── PREVOD (Srpski) ──────────────────────────────────")
                print(translated)
                print("────────────────────────────────────────────────────")
                print(f"✅ Prevod sačuvan: {t_path}")
            except Exception as e:
                print(f"❌ Prevod nije uspeo: {e}")

        if kljucne:
            print("🔑 Izvlačim ključne tačke…")
            try:
                prompt = (
                    "Izvuci ključne tačke iz sledećeg YouTube transkripta. "
                    "Formatiraj kao numerisanu listu na srpskom jeziku. Budi koncizan. "
                    "Ispiši samo listu, ništa drugo.\n\n"
                    f"{transcript_text}"
                )
                keypoints = call_gemini(api_key, prompt)
                kp_path = save_transcript(keypoints, suffix="_kljucne_tacke")
                print("\n── KLJUČNE TAČKE ────────────────────────────────────")
                print(keypoints)
                print("────────────────────────────────────────────────────")
                print(f"✅ Ključne tačke sačuvane: {kp_path}")
            except Exception as e:
                print(f"❌ Greška pri izvlačenju ključnih tačaka: {e}")


if __name__ == "__main__":
    main()
