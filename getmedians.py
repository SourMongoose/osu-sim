import os

def get_median(dist_file):
    angles = []
    times = []
    dists = []
    with open(dist_file, 'r') as f:
        lines = f.readlines()
    for l in lines:
        ls = l.split(',')
        angles.append(float(ls[0]))
        times.append(float(ls[1]))
        dists.append(float(ls[2]))

    angles.sort()
    times.sort()
    dists.sort()

    return angles[len(angles)//2], times[len(times)//2], dists[len(dists)//2]

def get_medians(medians_file='medians.txt'):
    medians = {}
    try:
        with open(medians_file, 'r') as f:
            lines = f.readlines()
        for i in range(0, len(lines), 2):
            medians[lines[i].strip()] = tuple(float(x) for x in lines[i+1].split(','))
    except:
        pass

    return medians

if __name__ == '__main__':
    medians = get_medians()

    dists_dir = 'dists'
    cnt = 0
    for entry in os.scandir(dists_dir):
        if entry.is_file() and entry.name not in medians:
            median = get_median(entry.path)
            medians[entry.name] = median

            cnt += 1
            if cnt % 100 == 0:
                print(cnt)

    with open('medians.txt', 'w', encoding='utf8') as f:
        for name in medians:
            f.write(name + '\n' + ','.join(str(x) for x in medians[name]) + '\n')
