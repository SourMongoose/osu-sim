mods_change = [['EZ'], ['HD'], ['HR'], ['HT'], ['DT', 'NC'], ['FL']]
def simplify_mods(mods):
    mods = mods.upper()
    modstring = ''
    for mod_group in mods_change:
        if any(mod in mods for mod in mod_group):
            modstring += mod_group[0]
    return modstring

def avg(lst):
    if not lst:
        return 0
    lst = list(lst)
    return sum(lst) / len(lst)

def overweight(m):
    id, mods, num_scores, avg_weight, avg_pp, max_pp = m
    return min(num_scores, 100) / 100 * avg_weight

def find_pp_maps(min_pp=0., max_pp=2e9, mods_include='', mods_exclude='', limit=100):
    mods_include, mods_exclude = simplify_mods(mods_include), simplify_mods(mods_exclude)

    def filter_func(m):
        if mods_include and m[1] != mods_include:
            return False
        if mods_exclude:
            for i in range(0, len(mods_exclude), 2):
                if mods_exclude[i:i+2] in m[1]:
                    return False
        return min_pp <= m[4] <= max_pp

    filtered_maps = list(filter(filter_func, map_list))
    filtered_maps.sort(key=lambda m: -overweight(m))

    return filtered_maps[:limit]

with open('maplist_pp.txt', 'r') as f:
    lines = f.readlines()

map_list = []
for line in lines:
    ls = line.split(',')
    map_list.append((ls[0], ls[1], int(ls[2]), float(ls[3]), float(ls[4]), float(ls[5])))

if __name__ == '__main__':
    with open('mapids_pp.txt', 'r') as f:
        lines = f.readlines()

    maps = {}

    for l in lines:
        id, idx, mods, pp, ts = l.split(',')
        mods = simplify_mods(mods)

        if id not in maps:
            maps[id] = {}
        if mods not in maps[id]:
            maps[id][mods] = []

        maps[id][mods].append((int(idx), float(pp), ts))

    map_list = []
    for id in maps:
        for mods in maps[id]:
            map_list.append((id, mods, len(maps[id][mods]), avg(0.95 ** score[0] for score in maps[id][mods]),
                             avg(score[1] for score in maps[id][mods]), max(score[1] for score in maps[id][mods])))

    with open('maplist_pp.txt', 'w') as f:
        f.write('\n'.join(','.join(str(x) for x in m) for m in map_list))
