import math
import os

def get_buckets(dist_file, output_file=None):
    if output_file is None:
        output_file = dist_file + '.bkts'

    buffer = 2 #ms

    buckets = {}
    sums = {}

    with open(dist_file, 'r') as f:
        lines = f.readlines()
    cnt = len(lines)

    n_a = 10
    n_d = 32
    s_a = 180 / n_a
    s_d = 640 / n_d

    for l in lines:
        ls = l.split(',')
        a, t, d = float(ls[0]), int(ls[1]), float(ls[2])

        for u in range(t-buffer, t+buffer+1):
            if u in buckets:
                t = u
                break

        if t not in buckets:
            buckets[t] = [[0]*n_d for _ in range(n_a)]
            sums[t] = 0

        b_a = math.floor(a / s_a) if a < 180 else n_a - 1
        b_d = math.floor(d / s_d) if d < 640 else n_d - 1
        b_d = math.floor((1 - (b_d / (n_d - 1)) ** 2) * (n_d - 1))
        buckets[t][b_a][b_d] += 1 / cnt
        sums[t] += 1

    with open(output_file, 'w') as f:
        for t in buckets:
            if sums[t] / cnt > 0.02:
                f.write(f'{t}\n{buckets[t]}\n')

    return output_file

def get_buckets_raw(dist):
    buffer = 2  # ms

    buckets = {}
    sums = {}

    lines = dist.split('\n')
    cnt = len(lines)

    n_a = 10
    n_d = 32
    s_a = 180 / n_a
    s_d = 640 / n_d

    for l in lines:
        if not l:
            break

        ls = l.split(',')
        a, t, d = float(ls[0]), int(ls[1]), float(ls[2])

        for u in range(t - buffer, t + buffer + 1):
            if u in buckets:
                t = u
                break

        if t not in buckets:
            buckets[t] = [[0] * n_d for _ in range(n_a)]
            sums[t] = 0

        b_a = math.floor(a / s_a) if a < 180 else n_a - 1
        b_d = math.floor(d / s_d) if d < 640 else n_d - 1
        b_d = math.floor((1 - (b_d / (n_d - 1)) ** 2) * (n_d - 1))
        buckets[t][b_a][b_d] += 1 / cnt
        sums[t] += 1

    for t in list(buckets.keys()):
        if sums[t] / cnt <= 0.02:
            buckets.pop(t)

    return buckets

if __name__ == '__main__':
    dists_dir = 'dists'
    buckets_dir = 'buckets'
    cnt = 0
    for entry in os.scandir(dists_dir):
        if entry.is_file():
            output_file = os.path.join(buckets_dir, entry.name)
            if os.path.exists(output_file):
                continue

            get_buckets(entry.path, output_file)

            cnt += 1
            if cnt % 100 == 0:
                print(cnt)
