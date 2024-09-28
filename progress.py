import re
import os
def reverse_readline(filename, buf_size=8192):
    with open(filename, 'r') as fh:
        segment = None
        offset = 0
        fh.seek(0, os.SEEK_END)
        file_size = remaining_size = fh.tell()
        while remaining_size > 0:
            if (offset >= file_size):
                break
            offset = min(file_size, offset + buf_size)
            fh.seek(file_size - offset)
            buffer = fh.read(min(remaining_size, buf_size))
            remaining_size -= buf_size
            lines = buffer.split('\n')
            if segment is not None:
                lines[-1] += segment
            segment = lines[0]
            for index in range(len(lines) - 1, 0, -1):
                if lines[index]:
                    yield lines[index]
        if segment is not None:
            yield segment

def clear_log_file(log_file='/var/log/apache2/error.log'):
    with open(log_file, 'w'):
        pass

def find_progress_with_ip(ip_address, log_file='/var/log/apache2/error.log'):
    for line in reverse_readline(log_file):
        client_string = f'[client {ip_address}'
        if client_string in line and '%' in line:
            progress = re.search(r'(\d+)%', line)
            if progress and progress.group() != '0%':
                return str(progress.group())
    return 'Preprocessing'

