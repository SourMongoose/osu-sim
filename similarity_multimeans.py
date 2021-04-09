import os
import math

import calc
import getmaps
import getmultimeans

def manhattan(a, b):
    return sum(abs(a[i] - b[i]) for i in range(len(a)))

def euclidean(a, b):
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(len(a))))

def get_multimean(multimean_file):
    multimean = {}
    with open(multimean_file, 'r') as f:
        lines = f.readlines()
        for l in lines:
            ls = l.split(',')
            multimean[int(ls[0])] = [float(ls[1]), float(ls[2]), float(ls[3])]
    return multimean

def get_similarity(m1, m2):
    aw = 0.5 # angle weight
    dw = 180 # distance weight
    tol = 0.05 # ms tolerance (% of time)

    sim = 0
    for t1 in m1:
        for t2 in m2:
            tol_ms = (t1 + t2) / 2 * tol
            t_corr = min(max(0, 10 + tol_ms - abs(t1 - t2)), 10) / 10
            mean_corr = math.pow(2, -manhattan((m1[t1][0]*aw, m1[t1][1]/t1*dw), (m2[t2][0]*aw, m2[t2][1]/t2*dw)) / 15)
            freq_corr = min(m1[t1][2], m2[t2][2])
            sim += t_corr * mean_corr * freq_corr
    return sim

def get_similar(id, n=50):
    _, text = getmaps.get_map(id)
    with open('temp.txt', 'w', encoding='utf8', newline='') as f:
        f.write(text)
    mm = get_multimean(getmultimeans.get_multimean(calc.get_distribution('temp.txt')))

    similarities = []

    mm_dir = 'means'
    cnt = 0
    for entry in os.scandir(mm_dir):
        if entry.is_file():
            temp_mm = get_multimean(entry.path)
            similarities.append((entry.name, get_similarity(mm, temp_mm), temp_mm))
            cnt += 1
            #if cnt % 100 == 0:
            #    print(cnt)

    similarities.sort(key=lambda s: -s[1])
    for i in range(n):
        print(similarities[i])

get_similar(1932689)
