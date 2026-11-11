import streamlit as st
import os

st.set_page_config(page_title="Shorts Studio Pro", page_icon="🎬", layout="wide")

# Custom CSS for Warm Glassmorphism Theme
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
        /* Adding a subtle warm tint overlay */
        background-color: #fffaf0;
        background-image: radial-gradient(at 0% 0%, hsla(28, 100%, 74%, 0.4) 0px, transparent 50%),
                          radial-gradient(at 100% 100%, hsla(11, 100%, 75%, 0.4) 0px, transparent 50%);
        background-attachment: fixed;
    }

    /* Glassmorphism Containers */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background: rgba(255, 255, 255, 0.4);
        border-radius: 15px;
        padding: 10px 20px;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 8px 32px 0 rgba(230, 115, 0, 0.1);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        border-radius: 10px !important;
        background-color: transparent !important;
        color: #d97706 !important;
        font-weight: 600;
        border: none !important;
    }

    .stTabs [aria-selected="true"] {
        background: rgba(245, 158, 11, 0.2) !important;
        box-shadow: inset 0 0 10px rgba(255, 255, 255, 0.5);
    }

    /* Cards / Inputs */
    .stTextInput > div > div > input, 
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {
        background: rgba(255, 255, 255, 0.5) !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
        border-radius: 10px !important;
        color: #451a03 !important;
        backdrop-filter: blur(5px);
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: bold !important;
        box-shadow: 0 4px 15px rgba(217, 119, 6, 0.4) !important;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(217, 119, 6, 0.6) !important;
    }
    
    /* Headings */
    h1, h2, h3 {
        color: #78350f !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎬 High-End Shorts Studio")
st.markdown("*Zero-confusion, premium video generation engine.*")

tab_script, tab_voices, tab_director, tab_export = st.tabs([
    "📝 Script Editor", 
    "🎙️ Casting (Voices)", 
    "🎬 Director (Visuals)", 
    "🚀 Render & Export"
])

with tab_script:
    st.header("Dialogue Script")
    st.write("Write your script here. Format: `Name: Message`. You can add as many characters as you want to create a Group Chat!")
    
    script_language = st.selectbox("Script Language", ["English", "Telugu"], index=0)
    
    if script_language == "Telugu":
        st.info("💡 **Tip:** You can write in **Telugu script** or in **English letters (Tenglish)** like *'eeroju em curry chesaav'* or *'Thinnava, padukunnava'*. The engine automatically reads it in natural, fluent Telugu!")
        default_script = f"""Player: eeroju em curry chesaav?
Riya: Thinnava , padukunnava?
Rahul: ఏంట్రా అప్పుడే పెళ్ళి కూడా అయిపోయిందా!
Player: Sare... bed meeda naa vaipu edi?
Riya: Madhyalo!"""
    else:
        default_script = f"""Player: Hey... so I guess we are married now?
Riya: Yep. Hey husband.
Rahul: Wait you guys got married without me?!
Player: So... which side of the bed is mine?
Riya: The middle."""
    
    script_text = st.text_area("Script", default_script, height=300)
    
    # Parse characters
    lines = script_text.strip().split('\n')
    characters = set()
    for line in lines:
        if ':' in line:
            characters.add(line.split(':')[0].strip())
    characters = list(characters)

with tab_voices:
    st.header("Character Casting")
    st.write("Select a built-in voice or upload a 5-second reference audio to clone any voice.")
    
    KOKORO_VOICES = ["am_adam", "af_bella", "af_sarah", "am_michael", "af_nicole", "af_sky"]
    TELUGU_VOICES = [
        "Telugu Male 1 (Mohan)", 
        "Telugu Female 1 (Shruti)", 
        "Telugu Male 2 (Mohan Deeper)", 
        "Telugu Female 2 (Shruti Lively)", 
        "Custom Voice Clone (Upload)"
    ]
    
    voice_map_state = {}
    
    if not characters:
        st.warning("Write some dialogue in the Script Editor to assign voices!")
    
    cols = st.columns(2)
    for i, char in enumerate(characters):
        with cols[i % 2]:
            st.subheader(f"🗣️ {char}")
            
            if script_language == "Telugu":
                selected_voice = st.selectbox(f"Voice for {char}", TELUGU_VOICES, key=f"voice_{char}")
                
                # Show upload if custom
                if selected_voice == "Custom Voice Clone (Upload)":
                    audio = st.file_uploader(f"Upload Reference Audio for {char}", type=["wav", "mp3"], key=f"audio_{char}")
                    voice_map_state[char] = {"type": "indicf5", "audio": audio}
                else:
                    mapping = {
                        "Telugu Male 1 (Mohan)": "telugu_male_1",
                        "Telugu Female 1 (Shruti)": "telugu_female_1",
                        "Telugu Male 2 (Mohan Deeper)": "telugu_male_2",
                        "Telugu Female 2 (Shruti Lively)": "telugu_female_2"
                    }
                    ref_name = mapping[selected_voice]
                    voice_map_state[char] = {"type": "indicf5_builtin", "ref_name": ref_name}
                    st.audio(f"assets/voices/{ref_name}_preview.wav")
            else:
                selected_voice = st.selectbox(f"Voice for {char}", KOKORO_VOICES, index=0, key=f"voice_{char}")
                voice_map_state[char] = {"type": "kokoro", "voice": selected_voice}
                st.audio(f"assets/voices/{selected_voice}_preview.wav")

with tab_director:
    st.header("Visual Effects & Split-Screen")
    
    st.subheader("1. Background Gameplay")
    bg_video = st.file_uploader("Upload Background Video (Minecraft, GTA, etc.)", type=["mp4", "mov"])
    
    st.subheader("2. UI Customization")
    col3, col4 = st.columns(2)
    with col3:
        theme = st.selectbox("Chat Theme", ["WhatsApp Dark", "WhatsApp Light", "iMessage"])
        start_time = st.text_input("Chat Start Time", "11:42 PM")
    with col4:
        battery_pct = st.slider("Battery Percentage", 1, 100, 15)
        wifi_signal = st.selectbox("Connection", ["WiFi", "5G", "4G", "None"])
        
    st.subheader("3. Audio Mix")
    enable_sfx = st.checkbox("Enable Authentic SFX (Typing, Swooshes)", value=True)

with tab_export:
    st.header("Render Pipeline")
    
    resolution = st.selectbox("Output Format", ["1080x1920 (Shorts/Reels)", "1080x1080 (Square)", "1920x1080 (Landscape)"])
    quality = st.selectbox("Render Quality", ["High (Faster)", "Maximum (ProRes/Lossless)"])
    
    if st.button("🚀 GENERATE VIRAL VIDEO", use_container_width=True):
        st.info("Render engine started... Please wait.")
        
        # Save script to a temp file
        script_path = "temp_ui_script.txt"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_text)
            
        import json
        import subprocess
        
        final_voice_map = {}
        for char, vdata in voice_map_state.items():
            if vdata["type"] == "kokoro":
                final_voice_map[char] = vdata["voice"]
            elif vdata["type"] == "indicf5_builtin":
                ref_path = f"assets/voices/{vdata['ref_name']}_preview.wav"
                final_voice_map[char] = f"indicf5:{ref_path}"
            elif vdata["type"] == "indicf5":
                if vdata["audio"] is not None:
                    # Save reference audio to disk
                    ext = vdata["audio"].name.split('.')[-1]
                    ref_path = f"ref_{char}.{ext}"
                    with open(ref_path, "wb") as f:
                        f.write(vdata["audio"].getbuffer())
                    final_voice_map[char] = f"indicf5:{ref_path}"
                else:
                    st.warning(f"Warning: No reference audio uploaded for {char}. Falling back to default.")
                    final_voice_map[char] = "indicf5:assets/voices/am_adam_preview.wav"
                    
        voice_map_json = json.dumps(final_voice_map)
        
        # Build command
        theme_flag = "whatsapp" if "WhatsApp" in theme else "roblox"
        lang_flag = script_language.lower()
        
        # We need to escape quotes properly for Windows powershell/cmd
        escaped_json = voice_map_json.replace('"', '\\"')
        cmd = f'python cli.py --format chat --script "{script_path}" --output ui_render_v2.mp4 --title "UI Render" --theme {theme_flag} --language {lang_flag} --voice_map "{escaped_json}"'
        
        # Execute
        st.write(f"Executing: `{cmd}`")
        import subprocess
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        subprocess.run(cmd, env=env, shell=True)
        
        output_file = "output/ui_render_v2.mp4"
        if os.path.exists(output_file):
            st.success(f"Render Complete! Video saved to {output_file}")
            st.video(output_file)
        else:
            st.error("Render failed. The output video was not created. Please check if you uploaded reference audio for Telugu.")
