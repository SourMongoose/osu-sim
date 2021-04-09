import os
import requests
from time import sleep

def get_map(id):
    r = requests.get(f'https://osu.ppy.sh/osu/{id}', timeout=1)
    filename = r.headers['Content-Disposition']
    filename = filename[filename.index('filename')+9:].strip('\'"')
    return filename, r.text

if __name__ == '__main__':
    mapids_file = r'C:\Users\chris\Documents\Python Workspace\osurec\mapids_nodup.txt'
    maps_folder = 'maps'

    with open(mapids_file, 'r') as f:
        mapids = f.readlines()

    files = [entry.name for entry in os.scandir(maps_folder)]

    idx = 5170
    while idx < len(mapids):
        print(idx)
        try:
            filename, text = get_map(mapids[idx].strip())
        except:
            continue

        #if not os.path.exists(path):
        if filename not in files:
            with open(os.path.join(maps_folder, filename), 'w', encoding='utf8', newline='') as f:
                f.write(text)
        else:
            idx += 1
            continue

        idx += 1

        sleep(1)
