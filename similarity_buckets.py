import os
import math
import numpy as np
import random

import calc
import getmaps
import getbuckets

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
    chars = '1234567890qwertyuiopasdfghjklzxcvbnm'
    temp_filename = ''.join(chars[random.randrange(len(chars))] for _ in range(10)) + '.osu'

    filename, text = getmaps.get_map(id)
    with open(temp_filename, 'w', encoding='utf8', newline='') as f:
        f.write(text)
    dist_file = calc.get_distribution(temp_filename)
    bkts_file = getbuckets.get_buckets(dist_file)
    bkts = get_buckets(bkts_file)

    os.remove(temp_filename)
    os.remove(dist_file)
    os.remove(bkts_file)

    similarities = []

    bkts_dir = 'buckets'
    cnt = 0
    for entry in os.scandir(bkts_dir):
        if entry.is_file() and not entry.name.startswith(filename):
            temp_bkts = get_buckets(entry.path)
            similarities.append((entry.name, get_similarity(bkts, temp_bkts)))
            cnt += 1
            # if cnt % 100 == 0:
            #     print(cnt)

    similarities.sort(key=lambda s: -s[1])
    return similarities[:n]

if __name__ == '__main__':
    get_similar(771858)
