import os
import pytz
import json
import io
import openai
import requests
import time
import sys
import logging
import shutil
import stable_whisper
from werkzeug.utils import secure_filename
from flask import Flask, flash, request, redirect, url_for, send_file, session, render_template, jsonify
from check import allowed_file, convert, increment_subtitle_numbers
from celery import Celery
from progress import find_progress_with_ip, clear_log_file
from pydub import AudioSegment
import datetime
import pysrt
import socket
import urllib.request as urllib
from uuid import uuid4
import pyrebase
import whisper
from whisper.utils import get_writer
from flask_dance.contrib.google import make_google_blueprint, google
from firebase_admin import credentials, storage, initialize_app, auth, db
import firebase_admin
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from celery.result import AsyncResult
from dotenv import load_dotenv  # Import dotenv

# Load environment variables from .env
load_dotenv()
# Folder paths
UPLOAD_FOLDER = '/var/www/html/flaskapp/upload_folder'
DOWNLOAD_FOLDER = '/var/www/html/flaskapp/download_folder'

# Flask app initialization
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
app.secret_key = os.getenv('SECRET_KEY')

# Celery initialization
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# Firebase configuration
config = {
    'apiKey': os.getenv('FIREBASE_API_KEY'),
    'authDomain': os.getenv('FIREBASE_AUTH_DOMAIN'),
    'databaseURL': os.getenv('FIREBASE_DATABASE_URL'),
    'projectId': os.getenv('FIREBASE_PROJECT_ID'),
    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET'),
    'messagingSenderId': os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
    'appId': os.getenv('FIREBASE_APP_ID'),
    'measurementId': os.getenv('FIREBASE_MEASUREMENT_ID')
}

firebase = pyrebase.initialize_app(config)
cred = credentials.Certificate(os.getenv('FIREBASE_ADMIN_CREDENTIALS'))
firebase_admin.initialize_app(cred, {
    'databaseURL': os.getenv('FIREBASE_DATABASE_URL'),
    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')
})

bucket = storage.bucket()

# Load the model
model = stable_whisper.load_model('small')

# Celery periodic task for cleanup
@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(3600, cleanup_old_user_dirs.s(), name='Clean up every hour')


@celery.task
def cleanup_old_user_dirs():
    def cleanup_directory(directory):
        now = time.time()
        for dir_name in os.listdir(directory):
            full_dir_name = os.path.join(directory, dir_name)
            if os.path.isdir(full_dir_name):
                last_access_time = os.path.getatime(full_dir_name)
                last_modification_time = os.path.getmtime(full_dir_name)
                if max(last_access_time, last_modification_time) < now - 3600:
                    shutil.rmtree(full_dir_name, ignore_errors=True)

    cleanup_directory(UPLOAD_FOLDER)
    cleanup_directory(DOWNLOAD_FOLDER)


@celery.task
def process(filename, result_type, actual_name, language, initial_prompt, user_id, translate_to_english, timezone):
    convert(filename, user_id)
    name_only = filename.rsplit('.', 1)[0]
    audio = os.path.join(UPLOAD_FOLDER, user_id, name_only + '.mp3')
    actual_name_only = actual_name.rsplit('.', 1)[0]

    # Determine the task (transcription or translation)
    file_task = 'transcribe' if translate_to_english != 'yes' else 'translate'

    # Run the transcription/translation task
    result = model.transcribe(audio, verbose=False, initial_prompt=initial_prompt, task=file_task, vad=True)

    # Save the result in .srt format
    result.to_srt_vtt(audio[:-4] + '.srt', word_level=False)

    # Increment subtitle numbers if needed
    final_file_path = os.path.join(UPLOAD_FOLDER, user_id, name_only + '.' + result_type)
    increment_subtitle_numbers(final_file_path)

    # Upload the result to Firebase
    upload_file_to_db(user_id, final_file_path, name_only + '.' + result_type, actual_name_only, timezone)


def time_to_milliseconds(time_obj):
    return (time_obj.hours * 3600 + time_obj.minutes * 60 + time_obj.seconds) * 1000 + time_obj.milliseconds


def get_subtitle_times(srt_file, index):
    subs = pysrt.open(srt_file)
    subtitle = subs[index]
    start_time = time_to_milliseconds(subtitle.start)
    end_time = time_to_milliseconds(subtitle.end)
    return start_time, end_time


def get_time_in_timezone(timezone_str):
    user_timezone = pytz.timezone(timezone_str)
    current_time = datetime.datetime.now(pytz.utc)
    local_time = current_time.astimezone(user_timezone)
    return local_time.strftime('%Y/%m/%d %H:%M (%A)')


def upload_file_to_db(user_id, local_file_path, filename, actual_name_only, timezone):
    name, extension = os.path.splitext(filename)
    cloud_file_path_srt = f'{user_id}/{name}.srt'
    cloud_file_path_mp3 = f'{user_id}/{name}.mp3'

    # Upload to Firebase
    blob_srt = bucket.blob(cloud_file_path_srt)
    blob_srt.content_type = 'application/x-subrip'
    blob_srt.upload_from_filename(local_file_path[:-4] + '.srt')

    blob_mp3 = bucket.blob(cloud_file_path_mp3)
    blob_mp3.content_type = 'audio/mpeg'
    blob_mp3.upload_from_filename(local_file_path[:-4] + '.mp3')

    # Store metadata in Firebase Realtime Database
    ref = db.reference(f'/users/{user_id}/files/{name}')
    ref.set({
        'file_name': name,
        'actual_name': actual_name_only,
        'upload_time': get_time_in_timezone(timezone)
    })


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'uid' in session:
        uid = session['uid']
        if request.method == 'POST':
            initial_prompt = request.form.get('Initial_prompt')
            file = request.files.get('audioFile')
            translate_to_english = request.form.get('translate_to_english')
            filetype = 'srt'
            if file and allowed_file(file.filename):
                safe_filename = secure_filename(file.filename)
                unique_id = uuid4().hex + '.' + safe_filename.split('.')[-1]

                user_dir = os.path.join(UPLOAD_FOLDER, uid)
                os.makedirs(user_dir, exist_ok=True)
                os.chmod(user_dir, 0o770)

                file.save(os.path.join(user_dir, unique_id))
                language = ''
                timezone = session.get('timezone', 'UTC')
                task = process.delay(unique_id, filetype, file.filename, language, initial_prompt, uid, translate_to_english, timezone)

                # Store task in Firebase
                ref = db.reference('tasks')
                task_info = {
                    'uid': uid,
                    'task_id': str(task.id),
                    'filename': file.filename,
                    'status': 'PENDING'
                }
                ref.push(task_info)

                return 'success', 200
    return redirect(url_for('login'))


@app.route('/user_tasks/<string:uid>')
def user_tasks(uid):
    ref = db.reference('tasks')
    user_tasks = ref.order_by_child('uid').equal_to(uid).get()

    task_states = {}
    deleted_task_states = {}

    for task_key, task_info in user_tasks.items():
        task_id = task_info.get('task_id')
        filename = task_info.get('filename')
        task = AsyncResult(task_id, app=celery)
        task_state = str(task.state)

        if task_state in ['SUCCESS', 'FAILURE']:
            ref.child(task_key).delete()
            deleted_task_states[filename] = task_state
        else:
            task_states[filename] = task_state

    return jsonify(active_tasks=task_states, deleted_tasks=deleted_task_states), 200

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'uid' in session:
        user_id = session['uid']
        files_ref = db.reference(f'/users/{user_id}/files')
        files_snapshot = files_ref.get()
        files_data = []

        if files_snapshot:
            for file_data in files_snapshot.values():
                files_data.append(file_data)

        def get_datetime(file_data):
            return datetime.datetime.strptime(file_data['upload_time'], '%Y/%m/%d %H:%M (%A)')

        # Sort files by upload time in reverse order (most recent first)
        files_data = sorted(files_data, key=get_datetime, reverse=True)

        email = session['email']
        return render_template('dashboard.html', files=files_data, user_id=user_id, email=email)
    return redirect(url_for('login'))


@app.route('/display/<string:user_id>/<string:file_name>', methods=['GET', 'POST'])
def display_file(user_id, file_name):
    if 'uid' in session and session['uid'] == user_id:
        ref = db.reference(f'/users/{user_id}/files/{file_name}')
        snapshot = ref.get()

        if not snapshot:
            return 'File not found', 404

        file_name = snapshot.get('file_name')
        actual_name = snapshot.get('actual_name')
        upload_time = snapshot.get('upload_time')

        audio_file_name = file_name + '.mp3'
        srt_file_name = file_name + '.srt'
        
        audio_blob = bucket.blob(f'{user_id}/{audio_file_name}')
        srt_blob = bucket.blob(f'{user_id}/{srt_file_name}')

        audio_url = audio_blob.generate_signed_url(datetime.timedelta(seconds=300), method='GET')
        srt_url = srt_blob.generate_signed_url(datetime.timedelta(seconds=300), method='GET')

        # Download the SRT file
        response = requests.get(srt_url)
        srt_content = response.text

        # Parse the SRT content
        subs = pysrt.from_string(srt_content)
        transcript_data = [(str(sub.start), str(sub.end), sub.text) for sub in subs]

        return render_template('display_file.html', actual_name=actual_name, upload_time=upload_time, 
                               transcript_data=transcript_data, audio_url=audio_url)

    return 'Unauthorized', 403


@app.route('/download/<path:filename>', methods=['GET'])
def download(filename):
    uid = session.get('uid')
    if not uid:
        return redirect(url_for('login'))

    # Serve SRT file
    return send_file(os.path.join(app.config['DOWNLOAD_FOLDER'], uid, filename + '.srt'), as_attachment=True)


@app.route('/audio/<path:filename>', methods=['GET'])
def serve_audio(filename):
    uid = session.get('uid')
    if not uid:
        return redirect(url_for('login'))

    # Serve MP3 file
    return send_file(os.path.join(app.config['DOWNLOAD_FOLDER'], uid, filename + '.mp3'), as_attachment=False)


@app.route('/delete/<string:file_name>', methods=['DELETE'])
def delete_file(file_name):
    user_id = session.get('uid')
    if not user_id:
        return redirect(url_for('login'))

    # Delete file references in Firebase Realtime Database
    file_ref = db.reference(f'/users/{user_id}/files/{file_name}')
    file_data = file_ref.get()
    if not file_data:
        return 'File not found', 404

    # Delete from Firebase Storage
    audio_file_name = f'{file_name}.mp3'
    srt_file_name = f'{file_name}.srt'

    audio_blob = bucket.blob(f'{user_id}/{audio_file_name}')
    srt_blob = bucket.blob(f'{user_id}/{srt_file_name}')

    audio_blob.delete()
    srt_blob.delete()

    # Delete the reference in Firebase Realtime Database
    file_ref.delete()

    return 'File deleted', 200


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'uid' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        # Handle login (e.g., via Firebase Auth or another method)
        pass

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('uid', None)
    session.pop('email', None)
    session.pop('timezone', None)
    return redirect(url_for('login'))


@app.route('/')
def home():
    is_logged_in = 'uid' in session
    return render_template('home3.html', is_logged_in=is_logged_in, email=session.get('email'))


@app.route('/sessionLogin', methods=['GET', 'POST'])
def session_login():
    if request.method == 'POST':
        id_token = request.form.get('idToken')
        email = request.form.get('email')
        timezone = request.form.get('timezone')

        try:
            # Verify Firebase ID Token
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token['uid']
            session['email'] = email
            session['uid'] = uid
            session['timezone'] = timezone
            return redirect(url_for('dashboard'))
        except Exception as e:
            print(f"Error verifying ID token: {e}")
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/googleLogin', methods=['GET', 'POST'])
def google_login():
    if request.method == 'POST':
        id_token = request.form.get('idToken')
        email = request.form.get('email')
        timezone = request.form.get('timezone')

        try:
            # Verify Google ID Token
            idinfo = id_token.verify_oauth2_token(id_token, google_requests.Request())
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')

            # Verify and get the user details
            uid = idinfo['sub']
            session['email'] = email
            session['uid'] = uid
            session['timezone'] = timezone
            return redirect(url_for('dashboard'))
        except ValueError as e:
            print(f"Error verifying Google ID token: {e}")
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/reset_password')
def reset_password():
    return render_template('reset_password.html')


@app.route('/timeout')
def timeout():
    return render_template('timeout.html')


if __name__ == '__main__':
    app.run()
