from osu_sr_calculator.osu_sr_calculator import calculateStarRating

def get_sr(map):
    rating = calculateStarRating(returnAllDifficultyValues=True, filepath=map)
    return rating['nomod']['aim'], rating['nomod']['speed']

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
    raw = 'srs_raw.txt'
    start_line = 5
    end_line = 31613
    line_step = 2

    with open(raw, 'r', encoding='utf8') as f:
        lines = f.readlines()

    with open('srs.txt', 'w', encoding='utf8') as f:
        for i in range(start_line, end_line, line_step):
            line = lines[i]
            song = line[:160]
            song = song[song.index('-')+1:].strip()
            sr, aim, speed, combo, ar, od = (float(x) for x in line[161:].strip('\n║').split('│'))

            f.write(f'{song}\n{aim},{speed}\n')