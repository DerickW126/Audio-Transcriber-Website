import os, glob, shutil
import whisper
from whisper.utils import get_writer
import sys
import stable_whisper

UPLOAD_FOLDER = '/var/www/html/flaskapp/upload_folder'
DOWNLOAD_FOLDER = '/var/www/html/flaskapp/download_folder'
dic = {"max_line_width": 40, "max_line_count": 40, "highlight_words": ""}

def remove_file():
	for filename in os.listdir(UPLOAD_FOLDER):
	    filepath = os.path.join(UPLOAD_FOLDER, filename)
	    try:
	        shutil.rmtree(filepath)
	    except OSError:
	        os.remove(filepath)
	for filename in os.listdir(DOWNLOAD_FOLDER):
	    filepath = os.path.join(DOWNLOAD_FOLDER, filename)
	    try:
	        shutil.rmtree(filepath)
	    except OSError:
	        os.remove(filepath)


model = stable_whisper.load_model('tiny')
def write_file(audio, prompt, language=""):
    result = model.transcribe(audio, verbose=False, initial_prompt=prompt)
    result.to_srt_vtt(audio[:-4] + '.srt', word_level=False)


write_file(UPLOAD_FOLDER + '/' + '52fe4b81296d43a08c761dee26120454.mp3', "")
