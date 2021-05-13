import os
import math
import numpy as np
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

def get_similar(id, n=50):
    filename, text = getmaps.get_map(id)
    dist = calc.get_distribution_raw(text)
    bkts = getbuckets.get_buckets_raw(dist)

    chars = '1234567890qwertyuiopasdfghjklzxcvbnm'
    temp_filename = ''.join(chars[random.randrange(len(chars))] for _ in range(10)) + '.osu'
    with open(temp_filename, 'w', encoding='utf8', newline='') as f:
        f.write(text)
    sr = getsrs.get_sr_old(temp_filename)
    os.remove(temp_filename)

    similarities = []

    for file in all_buckets:
        if file.startswith(filename):
            continue

        key = file[:-9].lower()
        if key not in srs:
            continue
        if euclidean(srs[key], sr) <= 0.5:
            similarities.append((file, get_similarity(bkts, all_buckets[file]), euclidean(srs[key], sr)))

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

def get_srs(srs_file='srs.txt'):
    srs = {}
    try:
        with open(srs_file, 'r') as f:
            lines = f.readlines()
        for i in range(0, len(lines), 2):
            srs[lines[i].strip().lower()] = tuple(float(x) for x in lines[i+1].split(','))
    except:
        pass

    return srs

all_buckets = get_all_buckets()
srs = get_srs('srs_old.txt')

if __name__ == '__main__':
    print(get_similar(771858))
