import os

import calc

songs_dir = r'maps'

cnt = 0
for subdir, dirs, files in os.walk(songs_dir):
    for filename in files:
        path = subdir + os.sep + filename
        if path.endswith(".osu"):
            # try:
            sldr_output = 'sliders' + os.sep + filename + '.sldr'
            #if not os.path.exists(sldr_output):
            calc.get_sliders(path, sldr_output)
            # except:
            #     pass

            cnt += 1
            if cnt % 100 == 0:
                print(cnt)