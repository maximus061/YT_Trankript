# YT Transkript

A desktop application for fetching, translating, and summarizing YouTube video transcripts — built with Python and PyQt6.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green)
![Gemini](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-orange?logo=google)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## Features

- **Fetch transcripts** from any YouTube video by URL or video ID
- **Translate to Serbian** using Google Gemini AI
- **Extract key points** as a numbered list in Serbian
- **Playlist support** — process an entire YouTube playlist automatically
- Clean dark-themed GUI with live output log
- Saves all results as `.txt` files, organized by timestamp

---

## Requirements

- Python 3.10+
- A [Google Gemini API key](https://aistudio.google.com/apikey) _(free tier available)_
- [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) _(only required for playlist processing)_

---

## Installation

**1. Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/yt-transkript.git
cd yt-transkript
```

**2. Create and activate a virtual environment** _(recommended)_
```bash
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Install yt-dlp** _(for playlist support)_
```bash
pip install yt-dlp
```

---

## Usage

```bash
python main.py
```

### Single video
1. Paste a YouTube URL or video ID into the **VIDEO URL ILI ID** field
2. Enter your Gemini API key
3. Toggle **PREVOD** and/or **KLJUČNE TAČKE** as needed
4. Click **PREUZMI**

### Playlist
1. Switch to the **PLAYLISTA** tab
2. Paste a YouTube playlist URL
3. Enter your Gemini API key
4. Toggle options and click **POKRENI**

All output files are saved to a `transcripts/` folder next to the executable.

---

## Building a standalone executable

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "YT-Transkript" main.py
```

The compiled binary will be in the `dist/` folder.

> **Note:** `yt-dlp` must still be installed separately on the target machine for playlist support.

---

## Project Structure

```
yt-transkript/
├── main.py
├── script.py
├── playlist.py
├── requirements.txt
└── README.md

```

---

## API Key Setup

1. Visit [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign in with a Google account
3. Click **Create API Key**
4. Paste the key into the app's **GEMINI API KLJUČ** field

The key is never stored — it must be entered each time the app is launched.

---

## Tech Stack

| Layer | Technology |
|
| GUI -> PyQt6 |
| Transcript fetching -> youtube-transcript-api |
| AI translation & summarization -> Google Gemini 2.5 Flash |
| Playlist parsing -> yt-dlp |
| Packaging -> PyInstaller |

---
