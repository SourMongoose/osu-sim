from osu_sr_calculator.osu_sr_calculator import calculateStarRating

def get_sr(map, dt=False):
    rating = calculateStarRating(returnAllDifficultyValues=True, filepath=map, mods=['DT']) if dt else calculateStarRating(returnAllDifficultyValues=True, filepath=map)
    mod = 'DT' if dt else 'nomod'
    return rating[mod]['aim'], rating[mod]['speed']

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

if __name__ == '__main__':
    raw = 'srs_dt_raw.txt'
    start_line = 5
    line_step = 2

    with open(raw, 'r', encoding='utf8') as f:
        lines = f.readlines()

    with open('srs_dt.txt', 'w', encoding='utf8') as f:
        for i in range(start_line, len(lines), line_step):
            line = lines[i]
            if not line.strip():
                break
            song = line[:160]
            song = song[song.index('-')+1:].strip()
            sr, aim, speed, combo, ar, od = (float(x) for x in line[161:].strip('\n║').split('│'))

            f.write(f'{song}\n{aim},{speed}\n')