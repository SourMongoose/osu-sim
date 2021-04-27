import os
import requests
from time import sleep

def get_map(id):
    r = requests.get(f'https://osu.ppy.sh/osu/{id}', timeout=1)
    filename = r.headers['Content-Disposition']
    filename = filename[filename.index('filename')+9:].strip('\'"')
    return filename, r.text

if __name__ == '__main__':
    mapids_file = r'C:\Users\chris\Documents\Python Workspace\osurec\mapids_country_nodup.txt'
    maps_folder = 'maps'

    with open(mapids_file, 'r') as f:
        mapids = f.readlines()

    with open('filenames.txt', 'r') as f:
        files = f.readlines()
    files = set(files[i] for i in range(0, len(files), 2))

    idx = 0
    while idx < len(mapids):
        print(idx)

        if mapids[idx] in files:
            idx += 1
            continue

        try:
            filename, text = get_map(mapids[idx].strip())
        except:
            continue

        with open('filenames.txt', 'a', encoding='utf8') as f:
            f.write(mapids[idx] + filename + '\n')

        #if not os.path.exists(path):
        if filename not in files:
            with open(os.path.join(maps_folder, filename), 'w', encoding='utf8', newline='') as f:
                f.write(text)

        idx += 1
