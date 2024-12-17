from flask import Flask, request, jsonify, send_file, render_template
import pandas as pd
import os
import dns.resolver
import uuid
from werkzeug.utils import secure_filename
import threading

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
progress = {}

# Ensure upload and processed directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def identify_esp(email):
    domain = email.split('@')[-1].lower()
    if domain in ['gmail.com', 'googlemail.com']:
        return 'Gmail'
    elif domain in ['outlook.com', 'hotmail.com', 'live.com', 'msn.com']:
        return 'Outlook'
    else:
        return identify_esp_from_mx(domain)

def identify_esp_from_mx(domain):
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        mx_record = str(mx_records[0].exchange).lower()
        if 'outlook' in mx_record or 'hotmail' in mx_record or 'live' in mx_record or 'office365' in mx_record:
            return 'Pro Outlook'
        elif 'google' in mx_record or 'gmail' in mx_record:
            return 'Pro Gmail'
        else:
            return 'Others'
    except Exception:
        return 'Others'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and file.filename.endswith('.csv'):
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        df = pd.read_csv(file_path)
        columns = df.columns.tolist()
        return jsonify({'file_path': filename, 'columns': columns})

    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/process', methods=['POST'])
def process_file():
    data = request.json
    if 'file_path' not in data or 'email_column' not in data:
        return jsonify({'error': 'Missing file path or email column'}), 400

    file_path = os.path.join(UPLOAD_FOLDER, data['file_path'])
    email_column = data['email_column']

    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    task_id = str(uuid.uuid4())
    progress[task_id] = 0

    def process_task():
        try:
            df = pd.read_csv(file_path)
        except pd.errors.ParserError as e:
            progress[task_id] = -1
            return

        if email_column not in df.columns:
            progress[task_id] = -1
            return

        total_rows = len(df)
        for index, row in df.iterrows():
            df.at[index, 'ESP'] = identify_esp(row[email_column])
            progress[task_id] = (index + 1) / total_rows * 100

        output_filename = f"{os.path.splitext(data['file_path'])[0]}-esp.csv"
        output_file = os.path.join(PROCESSED_FOLDER, output_filename)
        df.to_csv(output_file, index=False)
        
        progress[task_id] = 100

    threading.Thread(target=process_task).start()
    
    return jsonify({'task_id': task_id})

@app.route('/progress/<task_id>', methods=['GET'])
def get_progress(task_id):
    if task_id in progress:
        return jsonify({'progress': progress[task_id]})
    else:
        return jsonify({'error': 'Task not found'}), 404

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    file_path = os.path.join(PROCESSED_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
