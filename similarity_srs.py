import math
import os
import random

import getmaps
import getsrs

def manhattan(a, b):
    return sum(abs(a[i] - b[i]) for i in range(len(a)))

def get_similar(id, n=50):
    chars = '1234567890qwertyuiopasdfghjklzxcvbnm'
    temp_filename = ''.join(chars[random.randrange(len(chars))] for _ in range(10)) + '.osu'

    filename, text = getmaps.get_map(id)
    with open(temp_filename, 'w', encoding='utf8', newline='') as f:
        f.write(text)
    sr = getsrs.get_sr(temp_filename)

    os.remove(temp_filename)

    similarities = []

    for file in srs:
        if filename.startswith(file):
            continue

        similarities.append((file, manhattan(sr, srs[file])))

    similarities.sort(key=lambda s: s[1])
    return similarities[:n]

srs = getsrs.get_srs()

if __name__ == '__main__':
    print(get_similar(2118443))
