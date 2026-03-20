import os
import sys
import re
import json
import subprocess
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from google import genai


GEMINI_MODEL = "gemini-2.5-flash"


def call_gemini(api_key: str, prompt: str) -> str:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return response.text


def get_playlist_videos(playlist_url: str) -> list[dict]:
    """Returns list of {id, title} dicts using yt-dlp."""
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--flat-playlist",
                "--print", "%(id)s|||%(title)s",
                "--no-warnings",
                playlist_url,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        videos = []
        for line in result.stdout.strip().splitlines():
            if "|||" in line:
                vid_id, title = line.split("|||", 1)
                vid_id = vid_id.strip()
                title  = title.strip()
                if vid_id:
                    videos.append({"id": vid_id, "title": title})
        return videos
    except FileNotFoundError:
        print("❌ yt-dlp nije pronađen. Instalirajte ga sa: pip install yt-dlp")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("❌ Prekoračeno vreme pri učitavanju playliste.")
        sys.exit(1)


def sanitize_filename(name: str) -> str:
    """Remove characters unsafe for filenames."""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.replace(" ", "_")
    return name[:80]


def save_file(text: str, folder: str, filename: str) -> str:
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)
    return file_path


def process_video(video: dict, api_key: str, out_dir: str, prevod: bool, kljucne: bool):
    vid_id = video["id"]
    title  = video["title"]
    safe   = sanitize_filename(title) or vid_id

    print(f"\n🎬  [{vid_id}] {title}")

    # 1. Fetch transcript
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.fetch(vid_id)
        formatter = TextFormatter()
        transcript_text = formatter.format_transcript(transcript_list)
    except Exception as e:
        print(f"  ⚠  Transkript nije dostupan: {e}")
        return

    # Save original
    orig_path = save_file(transcript_text, out_dir, f"{safe}_original.txt")
    print(f"  ✅ Original sačuvan: {orig_path}")

    # 2. Prevod
    if prevod:
        print("  🌐 Prevodim na srpski…")
        try:
            prompt = (
                "Prevedi sledeći YouTube transkript na srpski jezik. "
                "Zadrži podele na pasuse. Ispiši samo prevedeni tekst, ništa drugo.\n\n"
                f"{transcript_text}"
            )
            translated = call_gemini(api_key, prompt)
            t_path = save_file(translated, out_dir, f"{safe}_srpski.txt")
            print(f"  ✅ Prevod sačuvan: {t_path}")
        except Exception as e:
            print(f"  ❌ Prevod nije uspeo: {e}")

    # 3. Ključne tačke
    if kljucne:
        print("  🔑 Izvlačim ključne tačke…")
        try:
            prompt = (
                "Izvuci ključne tačke iz sledećeg YouTube transkripta. "
                "Formatiraj kao numerisanu listu na srpskom jeziku. Budi koncizan. "
                "Ispiši samo listu, ništa drugo.\n\n"
                f"{transcript_text}"
            )
            keypoints = call_gemini(api_key, prompt)
            kp_path = save_file(keypoints, out_dir, f"{safe}_kljucne_tacke.txt")
            print(f"  ✅ Ključne tačke sačuvane: {kp_path}")
        except Exception as e:
            print(f"  ❌ Greška pri ključnim tačkama: {e}")


def main():
    # Usage: playlist.py <playlist_url> <apikey> [--prevod] [--kljucne]
    if len(sys.argv) < 3:
        print("Upotreba: python playlist.py <playlist_url> <apikey> [--prevod] [--kljucne]")
        sys.exit(1)

    playlist_url = None
    api_key      = None
    prevod       = False
    kljucne      = False

    for arg in sys.argv[1:]:
        if arg == "--prevod":
            prevod = True
        elif arg == "--kljucne":
            kljucne = True
        elif playlist_url is None:
            playlist_url = arg
        else:
            api_key = arg

    if not api_key:
        print("❌ API ključ je neophodan.")
        sys.exit(1)

    # Output folder: transcripts/playlist_YYYY-MM-DD_HH-MM-SS/
    script_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp  = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir    = os.path.join(script_dir, "transcripts", f"playlist_{timestamp}")

    print(f"📋 Učitavam playliste: {playlist_url}")
    videos = get_playlist_videos(playlist_url)

    if not videos:
        print("❌ Nije pronađen nijedan video u playlisti.")
        sys.exit(1)

    print(f"✅ Pronađeno videa: {len(videos)}")
    print(f"📁 Izlazni folder: {out_dir}")

    for i, video in enumerate(videos, 1):
        print(f"\n── Video {i}/{len(videos)} ──────────────────────────────────────")
        process_video(video, api_key, out_dir, prevod, kljucne)

    print(f"\n🏁 Obrada završena. Svi fajlovi su u: {out_dir}")


if __name__ == "__main__":
    main()
