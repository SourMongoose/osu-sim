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
    line = output.stdout.split(b'\n')[5]
    sr, aim, speed, combo, ar, od = (float(x) for x in line.strip(b'\xba').split(b'\xb3')[1:])
    return (aim, speed, sr)

def get_srs(srs_file='srs.txt'):
    srs = {}
    try:
        with open(srs_file, 'r') as f:
            lines = f.readlines()
        for i in range(0, len(lines), 2):
            srs[lines[i].strip()] = tuple(float(x) for x in lines[i+1].split(','))
    except:
        pass

    return srs

srs = get_srs()
srs_dt = get_srs('srs_dt.txt')
srs_hr = get_srs('srs_hr.txt')

if __name__ == '__main__':
    # print(get_sr_file('maps/Reol,nqrse - Ooedo Ranvu (zhu) [Normal].osu'))
    raw = 'srs_hr_raw.txt'
    start_line = 5
    line_step = 2

    with open(raw, 'r', encoding='utf8') as f:
        lines = f.readlines()

    with open('srs_hr.txt', 'w', encoding='utf8') as f:
        for i in range(start_line, len(lines), line_step):
            line = lines[i]
            if not line.strip():
                break
            song = line[:160]
            song = song[song.index('-')+1:].strip()

            # clean out illegal file chars
            for c in '?*/:"<>':
                song = song.replace(c, '')

            sr, aim, speed, combo, ar, od = (float(x) for x in line[161:].strip('\n║').split('│'))

            f.write(f'{song}\n{aim},{speed},{sr}\n')