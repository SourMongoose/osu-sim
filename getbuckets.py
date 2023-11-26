import math
import os

# Calculate the buckets for a beatmap
def get_buckets(dist_file, output_file=None):
    # If no output file is specified, create a .bkts file with the same name as the .dist file
    if output_file is None:
        output_file = dist_file + '.bkts'

    buffer = 2 #ms

    buckets = {}
    sums = {}

    # Read the .dist file
    with open(dist_file, 'r') as f:
        lines = f.readlines()
    cnt = len(lines)

    # Number of angle buckets
    n_a = 10
    # Number of distance buckets
    n_d = 32
    # Size of each angle bucket (180 degrees / 10 buckets = 18 degrees)
    s_a = 180 / n_a
    # Size of each distance bucket (640 units / 32 buckets = 20 units)
    s_d = 640 / n_d

    # For each line in the .dist file...
    for l in lines:
        # Split the line into angle, time, and distance
        ls = l.split(',')
        a, t, d = float(ls[0]), int(ls[1]), float(ls[2])

        # If the beat time is within 2ms of another beat time, set it to that beat time
        for u in range(t-buffer, t+buffer+1):
            if u in buckets:
                t = u
                break

        # If the beat time is not already in the buckets, add it as the key
        if t not in buckets:
            # Value is a 2d array of shape (10, 32) with all values initialized to 0
            buckets[t] = [[0]*n_d for _ in range(n_a)]
            # Value is the number of notes at that beat time (given the buffer)
            sums[t] = 0

        # If the angle is less than 180, divide it by the size of each angle bucket to get the bucket index
        # Otherwise, set the bucket index to the last bucket
        b_a = math.floor(a / s_a) if a < 180 else n_a - 1
        # If the distance is less than 640, divide it by the size of each distance bucket to get the bucket index
        # Otherwise, set the bucket index to the last bucket
        b_d = math.floor(d / s_d) if d < 640 else n_d - 1
        # Exponential scaling so there are more buckets near the lower end of the distance scale
        b_d = math.floor((1 - (b_d / (n_d - 1)) ** 2) * (n_d - 1))
        # Buckets is a 3D dictionary with the first key being the beat time, the second key being the angle bucket, and the third key being the distance bucket.
        # The value is normalized so that the theoretical maximum value for each bucket is 1.
        # Increment the value at the specified bucket by 1 / cnt
        buckets[t][b_a][b_d] += 1 / cnt
        # Increment the sum for the specified beat time by 1
        sums[t] += 1

    # Remove beat times with less than 2% of the total notes
    with open(output_file, 'w') as f:
        for t in buckets:
            if sums[t] / cnt > 0.02:
                # Write the beat time and then the associated angle/distance buckets
                f.write(f'{t}\n{buckets[t]}\n')

    return output_file

def get_buckets_raw(dist):
    buffer = 2  # ms

    buckets = {}
    sums = {}

    lines = dist.split('\n')
    cnt = len(lines)

    n_a = 10
    n_d = 32
    s_a = 180 / n_a
    s_d = 640 / n_d

    for l in lines:
        if not l:
            break

        ls = l.split(',')
        a, t, d = float(ls[0]), int(ls[1]), float(ls[2])

        for u in range(t - buffer, t + buffer + 1):
            if u in buckets:
                t = u
                break

        if t not in buckets:
            buckets[t] = [[0] * n_d for _ in range(n_a)]
            sums[t] = 0

        b_a = math.floor(a / s_a) if a < 180 else n_a - 1
        b_d = math.floor(d / s_d) if d < 640 else n_d - 1
        b_d = math.floor((1 - (b_d / (n_d - 1)) ** 2) * (n_d - 1))
        buckets[t][b_a][b_d] += 1 / cnt
        sums[t] += 1

    for t in list(buckets.keys()):
        if sums[t] / cnt <= 0.02:
            buckets.pop(t)

    return buckets

if __name__ == '__main__':
    dists_dir = 'dists'
    buckets_dir = 'buckets'
    cnt = 0
    # Iterate through all files in the "dists" directory
    for entry in os.scandir(dists_dir):
        # If it is a file...
        if entry.is_file():
            # Create a .bkts file if it doesn't already exist
            output_file = os.path.join(buckets_dir, entry.name)
            if os.path.exists(output_file):
                continue

            # Calculate the buckets for the beatmap
            get_buckets(entry.path, output_file)

            # Print the number of beatmaps processed so far
            cnt += 1
            if cnt % 100 == 0:
                print(cnt)
