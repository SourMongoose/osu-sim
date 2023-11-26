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
        path = subdir + os.sep + filename
        # If the file is an .osu file...
        if path.endswith(".osu"):
            try:
                # Create a .dist file for the beatmap
                dist_output = 'dists' + os.sep + filename[:-4] + '.dist'
                # If the .dist file doesn't already exist...
                if not os.path.exists(dist_output):
                    # Calculate the distribution of angles, time, and distance between notes
                    # Create a .dist file for the beatmap
                    calc.get_distribution(path, dist_output)
            except:
                pass

            # Print the number of beatmaps processed so far
            cnt += 1
            if cnt % 100 == 0:
                print(cnt)