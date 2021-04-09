import os

import calc

songs_dir = r'maps'

cnt = 0
for subdir, dirs, files in os.walk(songs_dir):
    for filename in files:
        path = subdir + os.sep + filename
        if path.endswith(".osu"):
            try:
                dist_output = 'dists' + os.sep + filename + '.dist'
                if not os.path.exists(dist_output):
                    calc.get_distribution(path, dist_output)
            except:
                pass

            cnt += 1
            if cnt % 100 == 0:
                print(cnt)