import os, json, hashlib, asyncio
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

PROJECT_DIR = Path(__file__).resolve().parent
AUDIO_DIR = PROJECT_DIR / "assets" / "audio"
IMAGE_DIR = PROJECT_DIR / "assets" / "images"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

async def generate_audio_edge(text: str, filename: str, voice: str = "en-US-AnaNeural"):
    import edge_tts
    communicate = edge_tts.Communicate(text, voice=voice, rate="-10%")
    await communicate.save(str(filename))

def ensure_audio(word: str) -> Path:
    safe_word = word.replace(" ", "_")
    audio_path = AUDIO_DIR / f"{safe_word}.mp3"
    if not audio_path.exists():
        asyncio.run(generate_audio_edge(word, audio_path))
    return audio_path

def parse_youtube_url(url: str) -> str:
    import re
    vid = None
    m = re.search(r"v=([a-zA-Z0-9_-]{11})", url)
    if m:
        vid = m.group(1)
    else:
        m = re.search(r"youtu\.be/([a-zA-Z0-9_-]{11})", url)
        if m:
            vid = m.group(1)
    if not vid:
        return ""
    return f"https://www.youtube.com/embed/{vid}?rel=0&modestbranding=1&controls=1"

CONFIG_FILE = PROJECT_DIR / "video_config.json"
def load_video_config() -> dict:
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"youtube_url": ""}
def save_video_config(url: str):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"youtube_url": url}, f)

def load_course_data() -> dict:
    data_file = PROJECT_DIR / "course_data.json"
    if not data_file.exists():
        st.error("course_data.json not found. Please generate it first.")
        return None
    with open(data_file, "r", encoding="utf-8") as f:
        return json.load(f)

def resolve_image_path(filename: str) -> Path:
    if not filename:
        return None
    p = IMAGE_DIR / filename
    if p.exists():
        return p
    alt = filename.replace(" ", "_")
    p2 = IMAGE_DIR / alt
    if p2.exists():
        return p2
    return p

def audio_button(word: str, label: str = "🔊 Listen", key_suffix: str = ""):
    if key_suffix:
        btn_key = f"play_{key_suffix}"
    else:
        btn_key = f"play_{hashlib.md5(word.encode()).hexdigest()[:10]}"
    audio_path = ensure_audio(word)
    clicked = st.button(label, key=btn_key)
    if clicked:
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        st.audio(audio_bytes, format="audio/mp3", autoplay=True)

def recorder_widget(placeholder_text: str, key_suffix: str = ""):
    uid = "rec_" + (key_suffix or str(hash(placeholder_text))[:8])
    html = f"""
    <div>
        <button id="voiceBtn_{uid}" onclick="toggleVoice_{uid}()" style="
            padding:16px 32px; font-size:24px; border:none; border-radius:16px;
            background:#66bb6a; color:white; cursor:pointer; font-weight:bold;
            width:100%; max-width:350px; box-shadow:0 4px 8px rgba(0,0,0,0.15);
            margin:8px 0;
        ">🎤 Start Speaking</button>
        <span id="voiceStatus_{uid}" style="margin-left:12px; font-size:20px; color:#555;"></span>
    </div>
    <script>
    var rec_{uid}=null; var isRecording_{uid}=false;
    function toggleVoice_{uid}() {{
        var btn = document.getElementById('voiceBtn_{uid}');
        var status = document.getElementById('voiceStatus_{uid}');
        if(isRecording_{uid}) {{
            if(rec_{uid}){{rec_{uid}.stop();rec_{uid}=null;}}
            isRecording_{uid}=false; btn.innerText='🎤 Start Speaking'; btn.style.background='#66bb6a'; return;
        }}
        var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if(!SR){{status.innerText='Browser does not support speech';return;}}
        rec_{uid}=new SR(); rec_{uid}.lang='en-US'; rec_{uid}.interimResults=false;
        rec_{uid}.continuous=false;
        rec_{uid}.onresult=function(e){{
            var transcript=e.results[0][0].transcript;
            status.innerText='✅ Recorded';
            try{{
                var pd=window.parent.document;
                var ta=pd.querySelector('textarea[placeholder*="{placeholder_text}"]');
                if(ta){{
                    var setter=Object.getOwnPropertyDescriptor(pd.defaultView.HTMLTextAreaElement.prototype,'value').set;
                    setter.call(ta,transcript);
                    ta.dispatchEvent(new Event('input',{{bubbles:true}}));
                    ta.dispatchEvent(new Event('change',{{bubbles:true}}));
                }}
            }}catch(e){{console.error(e);}}
            btn.innerText='🎤 Try Again'; btn.style.background='#66bb6a';
            isRecording_{uid}=false;
        }};
        rec_{uid}.onerror=function(){{
            status.innerText='Didn\\'t catch that. Try again.';
            btn.innerText='🎤 Start Speaking'; btn.style.background='#66bb6a';
            isRecording_{uid}=false;
        }};
        rec_{uid}.start();
        isRecording_{uid}=true;
        btn.innerText='⏹ Stop Recording'; btn.style.background='#ef5350';
        status.innerText='🎙️ Speak loudly...';
    }}
    </script>
    """
    components.html(html, height=80)

def rotate_image(image_path: Path, angle: int) -> Path:
    rotated_dir = IMAGE_DIR / "_rotated"
    rotated_dir.mkdir(exist_ok=True)
    new_name = f"{image_path.stem}_rot{angle}.png"
    new_path = rotated_dir / new_name
    if new_path.exists():
        return new_path
    img = Image.open(image_path)
    rotated = img.rotate(-angle, expand=True, fillcolor='white')
    rotated.save(new_path, optimize=True)
    return new_path