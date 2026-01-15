import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
from datetime import datetime

# --- 1. AUTHENTICATION ---
FOLDER_ID = "1YwtsUT_XKdLmX2rsYOn1ZGZXjKWSYU7b"
PASSWORD = "bigmansmallwomanhug"

try:
    info = dict(st.secrets["connections"]["gcs"]["service_account"])
    creds = service_account.Credentials.from_service_account_info(info)
    # Explicitly add the Drive Scope
    creds = creds.with_scopes(['https://www.googleapis.com/auth/drive'])
    service = build('drive', 'v3', credentials=creds)
except Exception as e:
    st.error(f"Auth Error: {e}")
    st.stop()

st.set_page_config(page_title="V&K Private Diary")

# --- LOGIN GATE ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    st.title("🔒 Private Entry")
    guess = st.text_input("Secret Code", type="password")
    if st.button("Unlock"):
        if guess == PASSWORD:
            st.session_state["auth"] = True
            st.rerun()
else:
    st.title("🎬 V&K Diary")
    user = st.radio("Who is recording?", ["Vardaan", "Krishneet"], horizontal=True)
    uploaded_file = st.file_uploader("📸 UPLOAD VIDEO", type=["mp4", "mov"])

  if uploaded_file is not None:
        with st.status("🚀 Uploading to Google Drive...") as status:
            # We convert the file to bytes
            file_bytes = uploaded_file.read()
            
            file_metadata = {
                'name': f"{datetime.now().strftime('%Y-%m-%d_%H-%M')}_{user}.mp4",
                'parents': [FOLDER_ID]
            }
            
            # Use a simpler upload method (non-resumable for smaller files/stability)
            media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype='video/mp4')
            
            try:
                file = service.files().create(
                    body=file_metadata, 
                    media_body=media, 
                    fields='id'
                ).execute()
                status.update(label="✅ Saved to Drive!", state="complete")
                st.balloons()
            except Exception as upload_error:
                st.error(f"Upload failed: {upload_error}")
                status.update(label="❌ Failed", state="error")
    st.divider()
    st.info("The feed is being synced. Refresh to see new videos!")

    # Function to list files in the folder
    def list_files():
        results = service.files().list(
            q=f"'{FOLDER_ID}' in parents", fields="files(id, name, webViewLink)").execute()
        return results.get('files', [])

    files = list_files()
    for f in sorted(files, key=lambda x: x['name'], reverse=True):
        st.write(f"📅 {f['name']}")
        st.video(f['webViewLink'])

