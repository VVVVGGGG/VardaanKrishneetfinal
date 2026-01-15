import streamlit as st
import os
from datetime import datetime

# --- 1. SETUP & CONFIG ---
PASSWORD = "bigmansmallwomanhug" 
# Removed H:/ BASE_DIR. Now it uses the folder where the script lives.
STORAGE_DIR = "diary_storage"
READ_MARKER_DIR = "read_receipts"

# Ensure folders exist (This works on Streamlit Cloud's temporary disk)
for folder in [STORAGE_DIR, READ_MARKER_DIR]:
    if not os.path.exists(folder): os.makedirs(folder)
for person in ["Vardaan", "Krishneet"]:
    path = os.path.join(STORAGE_DIR, person)
    if not os.path.exists(path): os.makedirs(path)

st.set_page_config(page_title="V&K Private Diary", layout="centered")

# --- CUSTOM CSS (Kept your original styles) ---
st.markdown("""
    <style>
    [data-testid="stFileUploadDropzone"] div div { display: none; }
    [data-testid="stFileUploadDropzone"] {
        border: 2px dashed #ff4b4b;
        background-color: #fff1f1;
        border-radius: 20px;
        height: 120px;
    }
    [data-testid="stFileUploadDropzone"]::before {
        content: "📸 TAP TO RECORD VIDEO";
        color: #ff4b4b;
        font-weight: bold;
        display: block;
        text-align: center;
        padding-top: 45px;
    }
    .stVideo { width: 100% !important; border-radius: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); }
    .seen-badge { color: #4BB543; font-weight: bold; font-size: 0.9em; background: #e8f5e9; padding: 2px 8px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIN GATE ---
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.title("🔒 Private Entry")
    guess = st.text_input("Enter Secret Code", type="password")
    if st.button("Unlock"):
        if guess == PASSWORD:
            st.session_state["auth"] = True
            st.rerun()
        else:
            st.error("Incorrect Password.")
else:
    # --- 3. MAIN APP ---
    st.title("🎬 V&K Diary")
    user = st.radio("Who is recording?", ["Vardaan", "Krishneet"], horizontal=True)

    uploaded_video = st.file_uploader("", type=["mp4", "mov", "avi"])

    if uploaded_video is not None:
        if "last_processed" not in st.session_state or st.session_state.last_processed != uploaded_video.name:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            file_name = f"{timestamp}_{user}.mp4"
            save_path = os.path.join(STORAGE_DIR, user, file_name)
            
            with open(save_path, "wb") as f:
                f.write(uploaded_video.getbuffer())
            
            st.session_state.last_processed = uploaded_video.name
            st.success("✅ Saved!")
            st.balloons()
            st.rerun()

    st.divider()
    t1, t2 = st.tabs(["Vardaan's Feed", "Krishneet's Feed"])

    def display_feed(person_name, viewer_name):
        path = os.path.join(STORAGE_DIR, person_name)
        if not os.path.exists(path): return
        
        vids = [f for f in os.listdir(path) if f.endswith(('.mp4', '.mov', '.avi'))]
        vids = sorted(vids, reverse=True)
        
        if not vids:
            st.info(f"No videos yet.")
            return

        for v in vids:
            marker_file = os.path.join(READ_MARKER_DIR, f"{v}.read")
            is_seen = os.path.exists(marker_file)
            
            col1, col2 = st.columns([0.7, 0.3])
            with col1: st.markdown(f"**📅 {v.split('_')[0]}**")
            with col2:
                if is_seen: st.markdown("<span class='seen-badge'>✓ Seen</span>", unsafe_allow_html=True)

            # Cloud-friendly video display
            video_file = open(os.path.join(path, v), 'rb')
            st.video(video_file.read())

            if viewer_name != person_name and not is_seen:
                if st.button(f"Mark Seen", key=f"seen_{v}"):
                    with open(marker_file, "w") as f:
                        f.write(f"Seen by {viewer_name}")
                    st.rerun()
            st.write("---")

    with t1: display_feed("Vardaan", user)
    with t2: display_feed("Krishneet", user)
