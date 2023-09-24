import json
import os
import subprocess

def get_sr(map, mods=None):
    if mods is None:
        mods = []

    if 'DT' in mods or 'NC' in mods:
        return srs_dt.get(map, None)
    elif 'HR' in mods:
        return srs_hr.get(map, None)
    return srs.get(map, None)

def get_sr_file(filename, mods=None):
    if mods is None:
        mods = []

    filename = os.path.join('../..', filename)
    cmd = ['dotnet', 'run', '--', 'difficulty', filename]
    if 'DT' in mods or 'NC' in mods:
        cmd.extend(['-m', 'dt'])
    elif 'HR' in mods:
        cmd.extend(['-m', 'hr'])

    output = subprocess.run(cmd, cwd='./osu-tools/PerformanceCalculator', stdout=subprocess.PIPE)
    line = output.stdout.split(b'\n')[5].decode('utf8')
    sr, aim, speed, combo, ar, od = (float(x) for x in line.strip('\u2551').split('\u2502')[1:])
    return (sr, aim, speed)

def get_srs(srs_file='srs.json'):
    with open(srs_file, 'r') as f:
        srs = json.load(f)
    return srs

srs = get_srs()
srs_dt = get_srs('srs_dt.json')
srs_hr = get_srs('srs_hr.json')

if __name__ == '__main__':
    #print(get_sr_file('maps/Reol,nqrse - Ooedo Ranvu (zhu) [Normal].osu'))
    raw = 'srs_raw_nm.txt'
    output_file = 'srs.json'
    start_line = 8
    line_step = 2

    with open(raw, 'r', encoding='utf8') as f:
        lines = f.readlines()

    song_srs = {}
    for i in range(start_line, len(lines), line_step):
        line = lines[i]
        if not line.strip():
            break
        song = line[:160]
        if song.startswith('║-1'):
            song = song[2:]
        song = song[song.index('-')+1:].strip()

        sr, combo, aim, speed, snc, fd, sf, _, _ = ((float(x.replace(',', '')) if x else 0) for x in line[161:].strip('\n║').split('│'))

        song_srs[song] = (sr, aim, speed)

    output_srs = {}

    with open('stats.json', 'r') as f:
        stats = json.load(f)

    for map in stats:
        s = stats[map]
        if not s['artist']:
            s['artist'] = 'unknown artist'
        mapstr = f'{s["artist"]} - {s["title"]} ({s["creator"]})'
        if s['version']:
            mapstr += f' [{s["version"]}]'
        if mapstr in song_srs:
            output_srs[map] = song_srs[mapstr]
        else:
            print(map, mapstr)

    with open(output_file, 'w') as f:
        json.dump(output_srs, f)
