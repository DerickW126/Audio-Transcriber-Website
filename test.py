import stable_whisper
'''
model = stable_whisper.load_model('tiny')
audio = 'upload_folder/testt.mp3'
result = model.transcribe(audio, verbose=False, initial_prompt=initial_prompt)
result.to_srt_vtt(audio[:-4] + '.srt', word_level=False)
'''
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

# Usage
srt_file_path = 'upload_folder/testt.srt'
increment_subtitle_numbers(srt_file_path)

