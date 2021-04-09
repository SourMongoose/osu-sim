import os

def get_multimean(dist_file, output_file=None):
    if output_file is None:
        output_file = dist_file + '.mean'

    buffer = 2 #ms

    multimean = {}
    with open(dist_file, 'r') as f:
        lines = f.readlines()
    cnt = len(lines)

    for l in lines:
        ls = l.split(',')
        a, t, d = float(ls[0]), int(ls[1]), float(ls[2])

        for u in range(t-buffer, t+buffer+1):
            if u in multimean:
                t = u
                break

        if t not in multimean:
            multimean[t] = [0, 0, 0]

        multimean[t][0] += a
        multimean[t][1] += d
        multimean[t][2] += 1

    with open(output_file, 'w') as f:
        for t in multimean:
            multimean[t][0] /= multimean[t][2]
            multimean[t][1] /= multimean[t][2]
            multimean[t][2] /= cnt
            if multimean[t][2] > 0.02:
                f.write(f'{t},{multimean[t][0]},{multimean[t][1]},{multimean[t][2]}\n')

    return output_file

if __name__ == '__main__':
    dists_dir = 'dists'
    multimeans_dir = 'means'
    cnt = 0
    for entry in os.scandir(dists_dir):
        if entry.is_file():
            output_file = os.path.join(multimeans_dir, entry.name)
            if os.path.exists(output_file):
                continue

            get_multimean(entry.path, output_file)

            cnt += 1
            if cnt % 100 == 0:
                print(cnt)
