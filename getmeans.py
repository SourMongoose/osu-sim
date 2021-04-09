import os

def get_mean(dist_file):
    s_a = s_t = s_d = 0
    with open(dist_file, 'r') as f:
        lines = f.readlines()
    for l in lines:
        ls = l.split(',')
        s_a += float(ls[0])
        s_t += float(ls[1]) 
        s_d += float(ls[2])
    cnt = len(lines)

    return s_a / cnt, s_t / cnt, s_d / cnt

def get_means(means_file='means.txt'):
    means = {}
    try:
        with open(means_file, 'r') as f:
            lines = f.readlines()
        for i in range(0, len(lines), 2):
            means[lines[i].strip()] = tuple(float(x) for x in lines[i+1].split(','))
    except:
        pass

    return means

if __name__ == '__main__':
    means = get_means()

    dists_dir = 'dists'
    cnt = 0
    for entry in os.scandir(dists_dir):
        if entry.is_file() and entry.name not in means:
            mean = get_mean(entry.path)
            means[entry.name] = mean

            cnt += 1
            if cnt % 100 == 0:
                print(cnt)

    with open('means.txt', 'w', encoding='utf8') as f:
        for name in means:
            f.write(name + '\n' + ','.join(str(x) for x in means[name]) + '\n')
