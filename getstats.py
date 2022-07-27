import os
import json

import calc

songs_dir = r'maps'

stats = {}

cnt = 0
for subdir, dirs, files in os.walk(songs_dir):
    for filename in files:
        path = subdir + os.sep + filename
        if path.endswith(".osu"):
            try:
                stats[filename] = calc.get_stats(path)
            except:
                pass

            cnt += 1
            if cnt % 100 == 0:
                print(cnt)

with open('stats.json', 'w') as fout:
    json.dump(stats, fout)
