import json
import math
import numpy as np
import os
import random

import calc
import getmaps
import getbuckets
import getsrs

def manhattan(a, b):
    return sum(abs(a[i] - b[i]) for i in range(len(a)))

def euclidean(a, b):
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(len(a))))

def get_buckets(buckets_file):
    buckets = {}
    with open(buckets_file, 'r') as f:
        lines = f.readlines()
        for i in range(0, len(lines), 2):
            buckets[int(lines[i])] = np.array(eval(lines[i+1]))
    return buckets

def kl_divergence(p, q):
    return np.sum(np.where(p*q != 0, np.log(p / q), 0))

def min_similarity(p, q):
    return np.sum(np.minimum(p, q))

def get_similarity(b1, b2):
    tol = 0.025 # ms tolerance (% of time)

    sim = 0
    for t1 in b1:
        for t2 in b2:
            tol_ms = (t1 + t2) / 2 * tol
            t_corr = min(max(0, 10 + tol_ms - abs(t1 - t2)), 10) / 10
            sim += t_corr * min_similarity(b1[t1], b2[t2])
    return sim

def get_similar(id, n=50, filters=None):
    text = getmaps.get_map(id)
    dist = calc.get_distribution_raw(text)
    bkts = getbuckets.get_buckets_raw(dist)

    key = str(id)
    if key in srs:
        sr = srs[key]
    else:
        chars = '1234567890qwertyuiopasdfghjklzxcvbnm'
        temp_filename = ''.join(chars[random.randrange(len(chars))] for _ in range(10)) + '.osu'
        with open(temp_filename, 'w', encoding='utf8', newline='') as f:
            f.write(text)
        sr = getsrs.get_sr_file(temp_filename)
        os.remove(temp_filename)

    similarities = []

    for file in all_buckets:
        if file.startswith(str(id)):
            continue

        if filters:
            valid = True
            for fil in filters:
                key, operator, value = fil
                funcs = {
                    '!=': lambda x, y: x != y,
                    '>=': lambda x, y: x >= y,
                    '<=': lambda x, y: x <= y,
                    '>': lambda x, y: x > y,
                    '<': lambda x, y: x < y,
                    '=': lambda x, y: x == y
                }
                if not funcs[operator](stats[file[:-5]][key], value):
                    valid = False
                    break
            if not valid:
                continue

        if not sr:
            similarities.append((file, get_similarity(bkts, all_buckets[file])))
        else:
            key = file[:-5]
            if key not in srs:
                continue

            if euclidean(srs[key][:2], sr[:2]) <= 0.5:
                similarities.append((file, get_similarity(bkts, all_buckets[file]), euclidean(srs[key][:2], sr[:2])))

    similarities.sort(key=lambda s: -s[1])
    return similarities[:min(len(similarities), n)]

def get_all_buckets():
    buckets = {}

    bkts_dir = 'buckets'
    for entry in os.scandir(bkts_dir):
        if entry.is_file():
            temp_bkts = get_buckets(entry.path)
            buckets[entry.name] = temp_bkts

    return buckets

all_buckets = get_all_buckets()
srs = getsrs.get_srs()
with open('stats.json') as fin:
    stats = json.load(fin)

if __name__ == '__main__':
    import time
    start = time.time()
    print(get_similar(2659353), time.time() - start)
