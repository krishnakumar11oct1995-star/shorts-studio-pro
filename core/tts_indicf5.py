import os
import asyncio
import concurrent.futures
import urllib.request
import json
import edge_tts
from edge_tts import Communicate

def is_telugu_script(text: str) -> bool:
    """Returns True if text already contains Telugu Unicode characters."""
    for char in text:
        if '\u0C00' <= char <= '\u0C7F':
            return True
    return False

def transliterate_tenglish_to_telugu(text: str) -> str:
    """
    Transliterates Roman script Telugu (Tenglish like 'eeroju em curry chesaav')
    into Telugu Unicode script ('ఈరోజు ఏం కర్రీ చేసావ్') using Google Input Tools.
    """
    if is_telugu_script(text):
        return text

    words = text.split()
    results = []
    for word in words:
        # Extract alphanumeric part
        clean = ''.join(c for c in word if c.isalnum())
        if not clean:
            results.append(word)
            continue
        
        # Don't transliterate numbers
        if clean.isdigit():
            results.append(word)
            continue

        url = f"https://inputtools.google.com/request?text={urllib.parse.quote(clean)}&itc=te-t-i0-und&num=1"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if data[0] == 'SUCCESS' and data[1] and data[1][0] and data[1][0][1]:
                    te_word = data[1][0][1][0]
                    results.append(word.replace(clean, te_word))
                else:
                    results.append(word)
        except Exception:
            results.append(word)
            
    return ' '.join(results)

def generate_indicf5_audio(text, ref_audio_path, ref_text, output_path, voice="telugu_male_1"):
    # If text is written in English script (Tenglish), transliterate to Telugu Unicode
    telugu_text = transliterate_tenglish_to_telugu(text)
    try:
        clean_preview = text[:30].encode('ascii', 'replace').decode('ascii')
        print(f"[TTS] ({voice}) Text: {clean_preview}...")
    except Exception:
        pass

    # Check if ref_audio_path contains a hint for the built-in voice
    if ref_audio_path:
        if "telugu_male_1" in ref_audio_path or "am_adam" in ref_audio_path:
            voice = "telugu_male_1"
        elif "telugu_female_1" in ref_audio_path or "af_bella" in ref_audio_path:
            voice = "telugu_female_1"
        elif "telugu_male_2" in ref_audio_path or "am_michael" in ref_audio_path:
            voice = "telugu_male_2"
        elif "telugu_female_2" in ref_audio_path or "af_sarah" in ref_audio_path:
            voice = "telugu_female_2"

    # Map our internal voice names to edge-tts voices and parameters
    voice_map = {
        "telugu_male_1": {"name": "te-IN-MohanNeural", "rate": "+0%", "pitch": "+0Hz"},
        "telugu_male_2": {"name": "te-IN-MohanNeural", "rate": "+0%", "pitch": "-10Hz"}, # Deeper
        "telugu_female_1": {"name": "te-IN-ShrutiNeural", "rate": "+0%", "pitch": "+0Hz"},
        "telugu_female_2": {"name": "te-IN-ShrutiNeural", "rate": "+0%", "pitch": "+10Hz"} # Higher
    }
    
    v_config = voice_map.get(voice, voice_map["telugu_male_1"])
    
    async def _generate():
        communicate = Communicate(
            telugu_text,
            v_config["name"],
            rate=v_config["rate"],
            pitch=v_config["pitch"]
        )
        await communicate.save(output_path)
        
    def _run_in_thread():
        asyncio.run(_generate())

    # Safely execute even inside an active asyncio event loop (e.g. Streamlit)
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as pool:
            pool.submit(_run_in_thread).result()
    else:
        _run_in_thread()

    return output_path

