from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import requests
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'supersecretkey'

FASTAPI_URL = 'http://127.0.0.1:8000'  # FastAPI backend URL


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    if file:
        response = requests.post(f"{FASTAPI_URL}/uploadfile", files={'file': (file.filename, file.stream, file.mimetype)})
        response_data = response.json()
        flash(f"File '{response_data.get('filename')}' uploaded successfully. File ID: {response_data.get('file_id')}. Status: {response_data.get('status')}", 'success')
    return redirect(url_for('index'))


@app.route('/delete', methods=['POST'])
def delete_file():
    file_id = request.form.get('file_id')
    if file_id:
        response = requests.delete(f"{FASTAPI_URL}/delete", params={'file_id': file_id})
        response_data = response.json()
        flash(f"File with ID {response_data.get('file_id')} deleted. Status: {response_data.get('status')}", 'danger')
    return redirect(url_for('index'))


@app.route('/update', methods=['POST'])
def update_file():
    file_id = request.form.get('file_id')
    file = request.files['file']
    if file_id and file:
        response = requests.put(f"{FASTAPI_URL}/update", params={'file_id': file_id}, files={'file': (file.filename, file.stream, file.mimetype)})
        response_data = response.json()
        flash(f"File '{response_data.get('filename')}' updated successfully. File ID: {response_data.get('file_id')}. Status: {response_data.get('status')}", 'warning')
    return redirect(url_for('index'))


@app.route('/retrieve', methods=['POST'])
def retrieve_file():
    file_id = request.form.get('file_id')
    filename = request.form.get('filename')
    params = {}
    if file_id:
        params['file_id'] = file_id
    elif filename:
        params['filename'] = filename

    if params:
        response = requests.get(f"{FASTAPI_URL}/retrieve", params=params)
        content_disposition = response.headers.get('Content-Disposition')
        if 'attachment' in content_disposition:
            file_name = content_disposition.split('filename=')[1].strip('"')
            file_content = BytesIO(response.content)  # Load the file content into memory
            return send_file(file_content, as_attachment=True, download_name=file_name)
        else:
            flash('File not found', 'danger')
    else:
        flash('Please provide either a file ID or filename', 'danger')

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
