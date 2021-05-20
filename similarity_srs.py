import math
import os
import random

import getmaps
import getsrs

def manhattan(a, b):
    return sum(abs(a[i] - b[i]) for i in range(len(a)))

def get_map_ids():
    map_ids = {}

    with open('filenames.txt', 'r') as f:
        lines = f.readlines()

    for i in range(0, len(lines), 2):
        map_ids[lines[i].strip()] = lines[i + 1].strip()[:-4]

    return map_ids

def get_similar(id, n=50, dt=False):
    to_use = srs_dt if dt else srs

    filename = map_ids.get(str(id), '')
    sr = to_use[filename] if filename in to_use else getsrs.get_sr(id, dt)

    # chars = '1234567890qwertyuiopasdfghjklzxcvbnm'
    # temp_filename = ''.join(chars[random.randrange(len(chars))] for _ in range(10)) + '.osu'
    #
    # filename, text = getmaps.get_map(id)
    # with open(temp_filename, 'w', encoding='utf8', newline='') as f:
    #     f.write(text)
    # sr = getsrs.get_sr(temp_filename, dt)
    #
    # os.remove(temp_filename)

    similarities = []

    for file in to_use:
        if filename.startswith(file):
            continue

        similarities.append((file, manhattan(sr, to_use[file])))

    similarities.sort(key=lambda s: s[1])
    return similarities[:n]

srs = getsrs.get_srs()
srs_dt = getsrs.get_srs('srs_dt.txt')

map_ids = get_map_ids()

if __name__ == '__main__':
    for x in get_similar(2118443, dt=True):
        print(x)
