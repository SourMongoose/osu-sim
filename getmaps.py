import os
import requests
from time import sleep

def get_map(id):
    r = requests.get(f'https://osu.ppy.sh/osu/{id}', timeout=1)
    return r.text

if __name__ == '__main__':
    mapids_file = 'mapids_nodup.txt'
    maps_folder = 'maps'

    with open(mapids_file, 'r') as f:
        mapids = [l.strip() for l in f.readlines()]

    existing = set(os.listdir(maps_folder))

    idx = 0
    fail = 0
    while idx < len(mapids):
        filename = f'{mapids[idx]}.osu'

        if filename in existing:
            idx += 1
            continue

        print(idx)

        try:
            text = get_map(mapids[idx].strip())
        except:
            fail += 1
            if fail >= 5:
                fail = 0
                idx += 1
            continue

        with open(os.path.join(maps_folder, filename), 'w', encoding='utf8', newline='') as f:
            f.write(text)

        idx += 1
