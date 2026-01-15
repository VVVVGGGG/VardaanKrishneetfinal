import streamlit as st
from st_files_connection import FilesConnection
from datetime import datetime
import os

# --- 1. SETUP & CONFIG ---
PASSWORD = "bigmansmallwomanhug" 

# Create the connection to Google Drive
# This requires st-files-connection and gcsfs in requirements.txt
conn = st.connection('gdrive', type=FilesConnection)

# Replace this with your Google Drive Folder ID (the long string in the folder URL)
GDRIVE_PATH = "gdrive://1YwtsUT_XKdLmX2rsYOn1ZGZXjKWSYU7b"

st.set_page_config(page_title="V&K Private Diary", layout="centered")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    [data-testid="stFileUploadDropzone"] {
        border: 2px dashed #ff4b4b;
        background-color: #fff1f1;
        border-radius: 20px;
        text-align: center;
    }
    .seen-badge { color: #4BB543; font-weight: bold; background: #e8f5e9; padding: 2px 8px; border-radius: 10px; }
    .stButton>button { width: 100%; border-radius: 12px; }
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

    uploaded_video = st.file_uploader("📸 TAP TO RECORD VIDEO", type=["mp4", "mov", "avi"])

    if uploaded_video is not None:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        file_name = f"{timestamp}_{user}.mp4"
        
        # Upload directly to Google Drive
        with st.spinner("Uploading to Google Drive..."):
            gdrive_target = f"{GDRIVE_PATH}/{user}/{file_name}"
            with conn.fs.open(gdrive_target, "wb") as f:
                f.write(uploaded_video.getbuffer())
            st.success("✅ Saved to Cloud!")
            st.balloons()

    st.divider()
    t1, t2 = st.tabs(["Vardaan's Feed", "Krishneet's Feed"])

    def display_feed(person_name, viewer_name):
        try:
            # List files from Google Drive folder
            vids = conn.fs.ls(f"{GDRIVE_PATH}/{person_name}")
            vids = [v for v in vids if v.endswith(('.mp4', '.mov', '.avi'))]
            vids = sorted(vids, reverse=True)
            
            if not vids:
                st.info(f"No videos yet.")
                return

            for v_path in vids:
                v_name = v_path.split('/')[-1]
                marker_file = f"{GDRIVE_PATH}/read_receipts/{v_name}.read"
                is_seen = conn.fs.exists(marker_file)
                
                st.markdown(f"**📅 {v_name.split('_')[0]}**")
                if is_seen:
                    st.markdown("<span class='seen-badge'>✓ Seen</span>", unsafe_allow_html=True)

                # Stream video from Drive
                with conn.fs.open(v_path, 'rb') as vf:
                    st.video(vf.read())

                if viewer_name != person_name and not is_seen:
                    if st.button(f"Mark Seen", key=f"seen_{v_name}"):
                        with conn.fs.open(marker_file, "w") as f:
                            f.write(f"Seen by {viewer_name}")
                        st.rerun()
                st.write("---")
        except Exception as e:
            st.error(f"Error connecting to Drive: {e}")

    with t1: display_feed("Vardaan", user)
    with t2: display_feed("Krishneet", user)
