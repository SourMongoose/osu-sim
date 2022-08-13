import getsrs

def manhattan(a, b):
    return sum(abs(a[i] - b[i]) for i in range(len(a)))

def get_similar(id, n=50, mods=None):
    if mods is None:
        mods = []

    if 'DT' in mods or 'NC' in mods:
        to_use = srs_dt
    elif 'HR' in mods:
        to_use = srs_hr
    else:
        to_use = srs

    filename = str(id)
    sr = to_use[filename]

    similarities = []

    for file in to_use:
        if filename.startswith(file):
            continue

        similarities.append((file, manhattan(sr, to_use[file])))

    similarities.sort(key=lambda s: s[1])
    return similarities[:n]

srs = getsrs.get_srs()
srs_dt = getsrs.get_srs('srs_dt.json')
srs_hr = getsrs.get_srs('srs_hr.json')

if __name__ == '__main__':
    for x in get_similar(2118443, mods=[]):
        print(x)
