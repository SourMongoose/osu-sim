import json

import getsrs

mods_change = [['NM'], ['EZ'], ['HD'], ['HR'], ['HT'], ['DT', 'NC'], ['FL']]
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

def get_map_info(id, mods):
    if id in map_dict:
        mods = simplify_mods(mods)
        if not mods:
            mods = 'NM'
        return map_dict[id].get(simplify_mods(mods), None)

def overweight_raw(m):
    id, mods, num_scores, avg_weight, avg_pp, max_pp = m
    return avg_weight

def overweight(m):
    id, mods, num_scores, avg_weight, avg_pp, max_pp = m
    return min(num_scores, 100) / 100 * avg_weight

def find_pp_maps(min_pp=0., max_pp=2e9, mods_include='', mods_exclude='', limit=100, filters=None):
    mods_include, mods_exclude = simplify_mods(mods_include), simplify_mods(mods_exclude)

    def get_stat(id, key):
        if key == 'id':
            return int(id)
        elif key in ['sr', 'star', 'stars']:
            return getsrs.get_sr(id)[0]
        elif key in ['aim', 'aimsr']:
            return getsrs.get_sr(id)[1]
        elif key in ['tap', 'tapsr']:
            return getsrs.get_sr(id)[2]
        elif id in stats and key in stats[id]:
            return stats[id][key]
        return None

    def filter_func(m):
        if filters:
            valid = True
            for fil in filters:
                key, operator, value = fil
                funcs = {
                    '!=': lambda x, y: x != y,
                    '>=': lambda x, y: x >= y,
                    '<=': lambda x, y: x <= y,
                    '>': lambda x, y: x > y,
                    '<': lambda x, y: x < y,
                    '=': lambda x, y: x == y
                }
                stat = get_stat(m[0], key)
                if not stat or not funcs[operator](stat, value):
                    valid = False
                    break
            if not valid:
                return False

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
map_dict = {}
for line in lines:
    ls = line.split(',')

    map_list.append((ls[0], ls[1], int(ls[2]), float(ls[3]), float(ls[4]), float(ls[5])))

    if ls[0] not in map_dict:
        map_dict[ls[0]] = {}
    map_dict[ls[0]][ls[1]] = (ls[0], ls[1], int(ls[2]), float(ls[3]), float(ls[4]), float(ls[5]))

with open('stats.json') as fin:
    stats = json.load(fin)

if __name__ == '__main__':
    with open('mapids_pp.txt', 'r') as f:
        lines = f.readlines()

    maps = {}

    for l in lines:
        id, idx, uid, mods, pp = l.split(',')
        mods = simplify_mods(mods)
        if not mods:
            mods = 'NM'

        if id not in maps:
            maps[id] = {}
        if mods not in maps[id]:
            maps[id][mods] = []

        maps[id][mods].append((int(idx), float(pp)))

    map_list = []
    for id in maps:
        for mods in maps[id]:
            map_list.append((id, mods, len(maps[id][mods]), avg(0.95 ** score[0] for score in maps[id][mods]),
                             avg(score[1] for score in maps[id][mods]), max(score[1] for score in maps[id][mods])))

    with open('maplist_pp.txt', 'w') as f:
        f.write('\n'.join(','.join(str(x) for x in m) for m in map_list))
