# Subttify

Subttify is a Flask-based web application that allows users to upload audio files, transcribe them using OpenAI's Whisper model, and optionally translate the transcription into English. The application integrates Google Firebase for user authentication and cloud storage.

## Features

- **File Upload:** Users can upload audio files for transcription.
- **Language Selection:** Users can choose the language of the audio before transcription.
- **Initial Prompt:** Users can provide an initial prompt to improve the accuracy of the transcription.
- **Translation Option:** Users can opt to translate their transcription to English.
- **Real-Time Notifications:** Users are notified when their transcription has been successfully processed.
- **User Dashboard:** Displays a list of uploaded files and their statuses.
- **Google Authentication:** Users can sign in using their Google accounts via Firebase Authentication.
- **Profile Management:** Users can view and manage their profile, including their profile picture and email.

## Demo / Tutorial Video

[![Watch the Demo](https://img.youtube.com/vi/i66a7zLniWQ/maxresdefault.jpg)](https://youtu.be/i66a7zLniWQ)

Click the image to watch the demo video on YouTube.

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
- A SendGrid account for email notifications (or any other email service provider)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/subttify.git
   cd subttify
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
FLASK_APP=flaskapp
FLASK_ENV=development
FIREBASE_CREDENTIALS=path/to/firebase_credentials.json
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
