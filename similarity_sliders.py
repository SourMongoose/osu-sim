import math
import os
import random

import calc
import getmaps
import getsrs

def euclidean(a, b):
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(len(a))))

def avg(lst):
    if not lst:
        return 0, 0
    return sum(p[0] for p in lst) / len(lst), sum(p[1] for p in lst) / len(lst)

def var(lst):
    if not lst:
        return 0, 0
    lst_avg = avg(lst)
    return sum((p[0] - lst_avg[0]) ** 2 for p in lst) / len(lst), sum((p[1] - lst_avg[1]) ** 2 for p in lst) / len(lst)

def std(lst):
    lst_var = var(lst)
    return math.sqrt(lst_var[0]), math.sqrt(lst_var[1])

def get_similarity(s1, s2):
    if not s1[0][0] or not s2[0][0]:
        return float('inf')

    avg1, avg2 = s1[0], s2[0]
    std1, std2 = s1[1], s2[1]
    similarity = abs(avg1[0] - avg2[0]) / (avg1[0] + avg2[0]) + abs(avg1[1] - avg2[1]) / (avg1[1] + avg2[1])
    # similarity += abs(std1[0] - std2[0]) / (std1[0] + std2[0]) + abs(std1[1] - std2[1]) / (std1[1] + std2[1])

    return similarity + abs(s1[2] - s2[2]) * 2

def get_similar(id, n=50):
    text = getmaps.get_map(id)
    sldr = calc.get_sliders_raw(text)

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

    for file in all_sliders:
        if file.startswith(key):
            continue

        if not sr:
            similarities.append((file, get_similarity(sldr, all_sliders[file])))
        else:
            key = file[:-5]
            if key not in srs:
                continue

            if euclidean(srs[key][:2], sr[:2]) <= 0.5:
                avg_sldr = avg(sldr[0])
                std_sldr = std(sldr[0])
                similarities.append((key, get_similarity((avg_sldr, std_sldr, sldr[1]), all_sliders[file]), euclidean(srs[key][:2], sr[:2])))

    similarities.sort(key=lambda s: s[1])
    return similarities[:min(len(similarities), n)]

def get_all_sliders():
    sliders = {}

    with open('sliderstats.txt', 'r', encoding='utf8') as f:
        lines = f.readlines()

    for i in range(0, len(lines), 2):
        filename = lines[i].strip()
        ls = [float(x) for x in lines[i+1].strip().split(',')]
        sliders[filename] = ((ls[0], ls[1]), (ls[2], ls[3]), ls[4])

    return sliders

all_sliders = get_all_sliders()
srs = getsrs.get_srs()

if __name__ == '__main__':
    inpt = ''
    while inpt != 'exit':
        inpt = input()
        print(get_similar(inpt))
        '''try:
            print(get_similar(inpt))
        except:
            continue'''