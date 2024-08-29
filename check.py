from pydub import AudioSegment
from moviepy.video.io.VideoFileClip import VideoFileClip
from werkzeug.utils import secure_filename
import subprocess

ALLOWED_EXTENSIONS = {'mp4', 'm4a', 'mp3', 'mov', 'mpeg', 'mpga', 'webm', 'wav'}
UPLOAD_FOLDER = '/var/www/html/flaskapp/upload_folder'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_audio(video_path, audio_path):
    command = "ffmpeg -i " + video_path + " -vn -acodec libmp3lame -threads 4 " + audio_path
    subprocess.call(command, shell=True)

def convert(filename, uid):
    name, extension = filename.rsplit('.', 1)
    video_path = UPLOAD_FOLDER + '/' + uid + '/' + filename
    audio_path = UPLOAD_FOLDER + '/' + uid + '/' + name + '.mp3'
    extract_audio(video_path, audio_path)

def increment_subtitle_numbers(srt_file_path):
    with open(srt_file_path, 'r') as file:
        lines = file.readlines()

    # Increment the subtitle numbers
    new_lines = []
    current_number = 0
    for line in lines:
        if line.strip() == str(current_number):
            new_lines.append(str(current_number + 1) + '\n')
            current_number += 1
        else:
            new_lines.append(line)

    # Write the modified content back to the file
    with open(srt_file_path, 'w') as file:
        file.writelines(new_lines)
