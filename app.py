import streamlit as st
import os
from datetime import datetime

# --- 1. SETUP & CONFIG ---
PASSWORD = "bigmansmallwomanhug" 
BASE_DIR = "H:/VardaanKrishneet"
STORAGE_DIR = os.path.join(BASE_DIR, "diary_storage")
READ_MARKER_DIR = os.path.join(BASE_DIR, "read_receipts")

# Ensure all folders exist on H: Drive
for folder in [STORAGE_DIR, READ_MARKER_DIR]:
    if not os.path.exists(folder): os.makedirs(folder)
for person in ["Vardaan", "Krishneet"]:
    path = os.path.join(STORAGE_DIR, person)
    if not os.path.exists(path): os.makedirs(path)

st.set_page_config(page_title="V&K Private Diary", layout="centered")

# --- CUSTOM CSS FOR MOBILE & UI ---
st.markdown("""
    <style>
    /* Style the upload box to look like a button */
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
    .stButton>button { width: 100%; border-radius: 12px; height: 3em; }
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
    
    # User Selection
    user = st.radio("Who is recording right now?", ["Vardaan", "Krishneet"], horizontal=True)

    st.subheader("Add to the Story")
    
    # Recording Tool (Triggers camera on phone)
    uploaded_video = st.file_uploader("", type=["mp4", "mov", "avi"])

    if uploaded_video is not None:
        # Check to prevent duplicate saves or saving to both folders
        if "last_processed" not in st.session_state or st.session_state.last_processed != uploaded_video.name:
            
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            file_name = f"{timestamp}_{user}.mp4"
            
            # Save specifically to the selected user's folder
            save_path = os.path.join(STORAGE_DIR, user, file_name)
            
            with open(save_path, "wb") as f:
                f.write(uploaded_video.getbuffer())
            
            # Lock this file in session state so it doesn't double-save
            st.session_state.last_processed = uploaded_video.name
            
            st.success(f"✅ Video saved to {user}'s folder!")
            st.balloons()
            st.rerun()

    st.divider()

    # --- 4. THE FEED & READ RECEIPTS ---
    t1, t2 = st.tabs(["Vardaan's Feed", "Krishneet's Feed"])

    def display_feed(person_name, viewer_name):
        path = os.path.join(STORAGE_DIR, person_name)
        if not os.path.exists(path): return
        
        # Get all video files
        vids = [f for f in os.listdir(path) if f.endswith(('.mp4', '.mov', '.avi'))]
        vids = sorted(vids, reverse=True) # Newest first
        
        if not vids:
            st.info(f"No videos from {person_name} yet.")
            return

        for v in vids:
            marker_file = os.path.join(READ_MARKER_DIR, f"{v}.read")
            is_seen = os.path.exists(marker_file)
            
            # Display Header
            col1, col2 = st.columns([0.7, 0.3])
            with col1:
                st.markdown(f"**📅 {v.split('_')[0]}**")
            with col2:
                if is_seen:
                    st.markdown("<span class='seen-badge'>✓ Seen</span>", unsafe_allow_html=True)

            # Display Video from H: Drive
            with open(os.path.join(path, v), 'rb') as vf:
                st.video(vf.read())

            # "Mark as Seen" Button
            # Only show if the current user is NOT the person who recorded it
            if viewer_name != person_name and not is_seen:
                if st.button(f"Mark Seen", key=f"seen_{v}"):
                    with open(marker_file, "w") as f:
                        f.write(f"Seen by {viewer_name} at {datetime.now()}")
                    st.rerun()
            st.write("---")

    with t1:
        display_feed("Vardaan", user)
    with t2:
        display_feed("Krishneet", user)