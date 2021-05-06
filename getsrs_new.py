import os

sr_dir = r'C:/Users/chris/Documents/stanriders/osu-tools/PerformanceCalculator/mapinfo'

cnt = 0
for entry in os.scandir(sr_dir):
    if entry.is_file():
        with open(entry.path, 'r', encoding='utf8') as f:
            lines = f.readlines()
        aim_sr = lines[5][10:-2].strip()
        tap_sr = lines[6][10:-2].strip()

        with open('srs.txt', 'a', encoding='utf8') as f:
            f.write(f'{entry.name[:-6]}\n{aim_sr},{tap_sr}\n')

        cnt += 1
        if cnt % 100 == 0:
            print(cnt)