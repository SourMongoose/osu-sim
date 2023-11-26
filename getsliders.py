import os

import calc

songs_dir = r'maps'

cnt = 0
# Iterate through all files in the "maps" directory
# Subdir is the path to the song folder
# Dirs is a list of subdirectories in the song folder (unused)
# Files is a list of beatmap files in the song folder
for subdir, dirs, files in os.walk(songs_dir):
    # For each beatmap...
    for filename in files:
        # Get the full path to the beatmap file
        path = os.path.join(subdir, filename)
        # If the file is an .osu file...
        if path.endswith(".osu"):
            try:
                # Create a .sldr file for the beatmap
                sldr_output = os.path.join('sliders', filename[:-4] + '.sldr')
                # If the .sldr file doesn't already exist...
                if not os.path.exists(sldr_output):
                    # Calculate the slider lengths, velocity, and total ratio
                    # Create a .sldr file for the beatmap
                    calc.get_sliders(path, sldr_output)
            except:
                pass

            # Print the number of beatmaps processed so far
            cnt += 1
            if cnt % 100 == 0:
                print(cnt)