# [Subttify](https://subttify.com) <img align="right" src="static/images/logo.png" alt="Subttify Logo" width="40">

Subttify is a Flask-based web application that allows users to upload audio files, transcribe them into substitle file (.srt) using OpenAI's Whisper model, and optionally translate the transcription into English. The application integrates Google Firebase for user authentication and cloud storage.

## Demo / Tutorial Video

Click the image to watch the demo video on YouTube.

[![Watch the Demo](https://img.youtube.com/vi/i66a7zLniWQ/maxresdefault.jpg)](https://youtu.be/i66a7zLniWQ)

## Features

- **File Upload:** Users can upload audio files for transcription.
- **Language Selection:** Users can choose the language of the audio before transcription.
- **Initial Prompt:** Users can provide an initial prompt to improve the accuracy of the transcription.
- **Translation Option:** Users can opt to translate their transcription to English.
- **Real-Time Notifications:** Users are notified when their transcription has been successfully processed.
- **User Dashboard:** Displays a list of uploaded files and their statuses.
- **Google Authentication:** Users can sign in using their Google accounts via Firebase Authentication.

## Tech Stack

### Backend:
- Flask
- Celery for task management and background processing
- Firebase for authentication and cloud storage
- OpenAI's Whisper model for transcription and translation

### Frontend:
- HTML/CSS with Bootstrap for responsive design
- JavaScript for real-time interaction and AJAX requests

## Setup Instructions

### Prerequisites

- Python 3.8+
- Firebase Project (with Authentication and Firestore enabled)
- OpenAI Whisper Model (ensure you have the appropriate setup to use this model locally)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/DerickW126/Audio-Transcriber-Website.git
```
   
2. Create a virtual environment and activate it:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up your Firebase and Whisper model credentials:

- Download your Firebase Admin SDK and place it in the project directory as firebase_credentials.json.
- Ensure you have Whisper set up locally (if running it locally), or configure access to the model via API.

5. Set up environment variables:

Create a .env file in the project root and add the following environment variables:
```bash
# Flask Secret Key
SECRET_KEY=your-secret-key-here

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Firebase Configuration
FIREBASE_API_KEY=your-firebase-api-key
FIREBASE_AUTH_DOMAIN=your-firebase-auth-domain
FIREBASE_DATABASE_URL=your-firebase-database-url
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_STORAGE_BUCKET=your-firebase-storage-bucket
FIREBASE_MESSAGING_SENDER_ID=your-firebase-messaging-sender-id
FIREBASE_APP_ID=your-firebase-app-id
FIREBASE_MEASUREMENT_ID=your-firebase-measurement-id

# Path to Firebase Admin SDK Credentials JSON
FIREBASE_ADMIN_CREDENTIALS=path/to/your/firebase-adminsdk-credentials.json
```

6. Run the application:

```bash
flask run
celery -A flaskapp.celery worker --loglevel=info
```

### Usage

1. **Sign in**: Use your Google account to sign in via Firebase Authentication.
2. **Upload a file**: Navigate to the "Upload your file" section and submit an audio file for transcription.
3. **Monitor progress**: Check the "Your Files" section to see the status of your uploads and view completed transcriptions.
4. **Receive notifications**: Get email alerts when your transcription is ready.

## Firebase Setup

To set up Firebase, follow these steps:

1. Go to the [Firebase Console](https://console.firebase.google.com/).
2. Create a new project.
3. Enable Authentication and choose Google as a sign-in method.
4. Enable Firestore (or Realtime Database if you're using that).
5. Download the Firebase Admin SDK and save it as `firebase_credentials.json` in your project.

## Whisper Model Setup

To set up OpenAI's Whisper model:

1. **Option 1: Local Setup**
   - Install Whisper by following the installation instructions [here](https://github.com/openai/whisper).
   - Ensure that Whisper is correctly installed in your environment and accessible to the backend process.
   
2. **Option 2: Remote API Setup**
   - If using Whisper via an API, ensure you have the appropriate access credentials and include them in your environment settings or code.

3. Modify your transcription logic to call the Whisper model for audio file processing.
