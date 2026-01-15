import streamlit as st
import gcsfs
from google.oauth2 import service_account
from datetime import datetime
import os

# --- 1. SETUP & AUTHENTICATION ---
# We use the direct GCSFS filesystem to avoid the 'refresh_token' error
try:
    # Build credentials from Streamlit Secrets
    info = dict(st.secrets["connections"]["gcs"]["service_account"])
    creds = service_account.Credentials.from_service_account_info(info)
    
    # Create the filesystem object directly
    # This acts as our direct bridge to Google Drive/GCS
    fs = gcsfs.GCSFileSystem(project=info.get("project_id"), token=creds)
except Exception as e:
    st.error(f"Authentication Setup Error: {e}")
    st.stop()

# Configuration
PASSWORD = "bigmansmallwomanhug" 
GDRIVE_PATH = "gcs://1YwtsUT_XKdLmX2rsYOn1ZGZXjKWSYU7b"

st.set_page_config(page_title="V&K Private Diary", layout="centered")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    [data-testid="stFileUploadDropzone"] {
        border: 2px dashed #ff4b4b;
        background-color: #fff1f1;
        border-radius: 20px;
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
        
        with st.status("🚀 Sending video to the cloud...", expanded=True) as status:
            gdrive_target = f"{GDRIVE_PATH}/{user}/{file_name}"
            
            # Using 'fs' directly to write the file
            with fs.open(gdrive_target, "wb") as f:
                f.write(uploaded_video.getbuffer())
                
            status.update(label="✅ Saved to Cloud!", state="complete", expanded=False)
            st.balloons()

    st.divider()
    t1, t2 = st.tabs(["Vardaan's Feed", "Krishneet's Feed"])

    def display_feed(person_name, viewer_name):
        try:
            folder_path = f"{GDRIVE_PATH}/{person_name}"
            
            # Use 'fs' to list and check files
            if not fs.exists(folder_path):
                fs.makedirs(folder_path)
                st.info(f"Folder created for {person_name}. No videos yet.")
                return

            vids = fs.ls(folder_path)
            vids = [v for v in vids if v.endswith(('.mp4', '.mov', '.avi'))]
            vids = sorted(vids, reverse=True)
            
            if not vids:
                st.info(f"No videos yet.")
                return

            for v_path in vids:
                v_name = v_path.split('/')[-1]
                # Ensure read_receipts folder exists
                receipt_dir = f"{GDRIVE_PATH}/read_receipts"
                if not fs.exists(receipt_dir): fs.makedirs(receipt_dir)
                
                marker_file = f"{receipt_dir}/{v_name}.read"
                is_seen = fs.exists(marker_file)
                
                st.markdown(f"**📅 {v_name.split('_')[0]}**")
                if is_seen:
                    st.markdown("<span class='seen-badge'>✓ Seen</span>", unsafe_allow_html=True)

                # Open and display video stream
                with fs.open(v_path, 'rb') as vf:
                    st.video(vf.read())

                if viewer_name != person_name and not is_seen:
                    if st.button(f"Mark Seen", key=f"seen_{v_name}"):
                        with fs.open(marker_file, "w") as f:
                            f.write(f"Seen by {viewer_name}")
                        st.rerun()
                st.write("---")
        except Exception as e:
            st.error(f"Feed Error: {e}")

    with t1: display_feed("Vardaan", user)
    with t2: display_feed("Krishneet", user)
