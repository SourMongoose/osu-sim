import math
# import matplotlib.pyplot as plt

def angle_between(x1, y1, x2, y2, x3, y3):
    a1 = math.atan2(y1 - y2, x1 - x2) * 180 / math.pi
    a2 = math.atan2(y3 - y2, x3 - x2) * 180 / math.pi
    diff = abs(a2 - a1)
    return min(diff, 360 - diff)

def distance_between(x1, y1, x2, y2):
    return math.sqrt((y2 - y1) * (y2 - y1) + (x2 - x1) * (x2 - x1))

# Get the distribution of angles, time, and distance between notes
def get_distribution(input_file, output_file=None):
    # Create a .dist output file to store the distribution
    if output_file is None:
        output_file = input_file + '.dist'

    # Open the beatmap file for reading
    with open(input_file, 'r', encoding='utf8') as fin:
        lines = fin.readlines()

    # Open the .dist output file for writing
    with open(output_file, 'w') as fout:
        # Find the line number of the first hit object line.
        i = lines.index('[HitObjects]\n') + 1
        # Initialize ??? to -1
        qx = qy = qt = zx = zy = zt = -1
        # Read all the lines in the HitObjects section
        while i < len(lines):
            # Example line: 64,320,5538,5,0,
            # Split the line and get 5 values
            vals = lines[i].split(',')
            # Increment the line number
            i += 1
            # Get the x position, y position, time, and type of hit object from the line
            x, y, t, type = int(vals[0]), int(vals[1]), int(vals[2]), int(vals[3])

            # If type = 0b0001, then the hit object is a circle
            circle = bool(type & (1 << 0))
            # If type = 0b0010, then the hit object is a slider
            slider = bool(type & (1 << 1))
            # If type = 0b1000, then the hit object is a spinner
            spinner = bool(type & (1 << 3))

            # If the hit object is a spinner,
            # do not calculate angles, time, and distance
            # between previous object to it and next object to it
            if spinner:
                qx = qy = qt = zx = zy = zt = -1
                continue

            # If the hit object is a slider,
            # do not calculate angles, time, and distance between previous object to it
            # but next objects can calculate angles, time, and distance to it
            if slider:
                pass

            # If the hit object is a circle and the previous-previous object was either a circle or a slider...
            if qx != -1:
                # Calculate the angle between the previous-previous object, the previous object, and the current object
                angle = angle_between(qx, qy, zx, zy, x, y)
                # Calculate the time between the previous object and the current object
                time = t - zt
                # Calculate the distance between the previous object and the current object
                dist = distance_between(zx, zy, x, y)
                # Write the angle, time, and distance to the .dist output file
                fout.write(f'{angle},{time},{dist}\n')

            # Set the previous-previous object to the previous object
            qx, qy, qt = zx, zy, zt
            # Set the previous object to the current object
            zx, zy, zt = x, y, t
    # Return the name of the .dist output file
    return output_file

def get_distribution_raw(input):
    lines = input.split('\r\n')

    output = ''

    i = lines.index('[HitObjects]') + 1
    qx = qy = qt = zx = zy = zt = -1
    while i < len(lines):
        if not lines[i]:
            break

        vals = lines[i].split(',')
        i += 1
        x, y, t, type = int(vals[0]), int(vals[1]), int(vals[2]), int(vals[3])

        circle = bool(type & (1 << 0))
        slider = bool(type & (1 << 1))
        spinner = bool(type & (1 << 3))

        if spinner:
            qx = qy = qt = zx = zy = zt = -1
            continue

        if slider:
            pass

        if qx != -1:
            angle = angle_between(qx, qy, zx, zy, x, y)
            time = t - zt
            dist = distance_between(zx, zy, x, y)
            output += f'{angle},{time},{dist}\n'

        qx, qy, qt = zx, zy, zt
        zx, zy, zt = x, y, t

    return output

"""
def graph_distribution(dist_file):
    x = []
    y = []
    z = []
    with open(dist_file, 'r') as f:
        lines = f.readlines()
        for l in lines:
            ls = l.split(',')
            angle, time, dist = float(ls[0]), int(ls[1]), float(ls[2])
            if time < 1000:
                x.append(angle)
                y.append(dist)
                z.append(time)

    plt.title(dist_file)
    ax = plt.axes(projection='3d')
    ax.set_xlabel('Angle')
    ax.set_ylabel('Distance')
    ax.set_zlabel('Time')
    plt.xlim(-10, 190)
    ax.scatter3D(x, y, z)
    plt.show()
"""

def get_sliders(input_file, output_file=None):
    # Create a .sldr output file to store the slider data
    if output_file is None:
        output_file = input_file + '.sldr'

    # Open the beatmap file for reading
    with open(input_file, 'r', encoding='utf8') as fin:
        lines = fin.readlines()

    # Get base slider velocity
    slider_mult = -1
    for line in lines:
        if line.startswith('SliderMultiplier'):
            slider_mult = float(line[line.index(':') + 1:]) * 100
            break

    beat_length = -1
    timing_points = []
    # Get the line number of the first timing point
    i = lines.index('[TimingPoints]\n') + 1
    # Read all the lines in the TimingPoints section
    while i < len(lines) and not lines[i].startswith('[') and lines[i].strip():
        # Example line: 377,-100,4,2,4,30,0,0
        ls = lines[i].split(',')
        # Timing points must have at least 8 values, append 0s if there are less
        while len(ls) < 8:
            ls.append(0)

        # Time: Start time of the timing section.
        #       End of the timing section is the next timing point's time.
        # Beat Length: For uninherited timing points, the duration of a beat in milliseconds.
        #              For inherited timing points, negative inverse slider velocity multiplier.
        #                Example: -50 makes all sliders in this timing section twice as fast as SliderMultiplier.
        # Uninherited: If uninherited, timing point has its own timing settings.
        #              If inherited, timing point inherits the timing settings from the previous timing point.
        time, beatLength, meter, sampleSet, sampleIndex, volume, uninherited, effects = (float(x) for x in ls)
        # Meter (unused): Number of beats in a measure. Inherited timing points ignores this value.
        # Sample Set (unused): Default sample set for hit objects (hitsound type).
        # Sample Index (unused): Custom sample index for hit objects. 0 indicates default hitsounds.
        # Volume (unused): Volume percentage for hit objects.
        # Effects (unused): Bit flags that give the timing point extra effects.

        # If the timing point is uninherited...
        if uninherited:
            # Beat length field gives the duration of a beat in milliseconds.
            beat_length = beatLength
            # Append the time of the start of the timing section and the slider velocity to the timing points list
            # Slider velocity is how far a slider travels in one beat
            timing_points.append((time, slider_mult / beat_length))
        # If the timing point is inherited...
        else:
            # Append the time of the start of the timing section and the adjusted slider velocity to the timing points list
            timing_points.append((time, slider_mult / beat_length * (-100 / beatLength)))

        # Increment the line number
        i += 1

    # The first timing point must have a time of 0.
    timing_points[0] = (0, timing_points[0][1])
    # Reverse the list of timing points
    timing_points = timing_points[::-1]

    # Open the .sldr output file for writing
    with open(output_file, 'w') as fout:
        slider_time = 0
        total_time = 0
        first_object = -1

        # Get the line number of the first hit object line.
        i = lines.index('[HitObjects]\n') + 1
        # Read all the lines in the HitObjects section
        while i < len(lines):
            # Check that the line is not empty
            if not lines[i].strip():
                i += 1
                continue

            # Example line: 256,86,291,2,0,L|256:18,2,42.5,8|4|2,0:0|0:0|0:0,0:0:0:0:
            # Split the line and get 8 values
            vals = lines[i].split(',')
            # Get the x position, y position, time, and type of hit object from the line
            x, y, t, type = int(vals[0]), int(vals[1]), int(vals[2]), int(vals[3])
            # Increment the line number
            i += 1

            # If type = 0b0001, then the hit object is a circle (unused)
            circle = bool(type & (1 << 0))
            # If type = 0b0010, then the hit object is a slider
            slider = bool(type & (1 << 1))
            # If type = 0b1000, then the hit object is a spinner
            spinner = bool(type & (1 << 3))

            # If the first object has not been set yet...
            if first_object == -1:
                # Set the first object to the current object's time
                first_object = t
            # Calculate the time between the first object and the current object
            total_time = t - first_object

            # If the hit object is a spinner, do not calculate slider time
            if spinner:
                continue

            # If the hit object is a slider...
            if slider:
                # Get the time of the hit object and the length of the slider
                x, y, time, type, hitSound, curve, slides, length = vals[:8]

                velocity = -1
                # Go through each timing point
                for point in timing_points:
                    # When you find the timing point the current slider object is in...
                    if float(time) > point[0]:
                        # Set the slider velocity to the slider velocity of the timing point
                        velocity = point[1]
                        # Stop searching through the timing points
                        break

                # Increment the total slider time by the current slider's time
                slider_time += float(length) / velocity

                # Write the slider length and slider velocity to the .sldr output file
                fout.write(f'{length.strip()}, {velocity}\n')

        # Write the slider time to total time ratio to the .sldr output file
        fout.write(f'{slider_time / total_time}\n')

    # Return the name of the .sldr output file
    return output_file

def get_sliders_raw(input):
    lines = input.split('\r\n')

    output = []

    slider_mult = -1
    for line in lines:
        if line.startswith('SliderMultiplier'):
            slider_mult = float(line[line.index(':') + 1:]) * 100
            break

    beat_length = -1
    timing_points = []
    i = lines.index('[TimingPoints]') + 1
    while i < len(lines) and not lines[i].startswith('[') and lines[i].strip():
        time, beatLength, meter, sampleSet, sampleIndex, volume, uninherited, effects = (float(x) for x in
                                                                                         lines[i].split(','))

        if uninherited:
            beat_length = beatLength
            timing_points.append((time, slider_mult / beat_length))
        else:
            timing_points.append((time, slider_mult / beat_length * (-100 / beatLength)))

        i += 1

    timing_points[0] = (0, timing_points[0][1])
    timing_points = timing_points[::-1]

    slider_time = 0
    total_time = 0
    first_object = -1

    i = lines.index('[HitObjects]') + 1
    while i < len(lines):
        if not lines[i].strip():
            i += 1
            continue

        vals = lines[i].split(',')
        x, y, t, type = int(vals[0]), int(vals[1]), int(vals[2]), int(vals[3])
        i += 1

        circle = bool(type & (1 << 0))
        slider = bool(type & (1 << 1))
        spinner = bool(type & (1 << 3))

        if first_object == -1:
            first_object = t
        total_time = t - first_object

        if spinner:
            continue

        if slider:
            x, y, time, type, hitSound, curve, slides, length = vals[:8]
            time = int(time)
            slides = int(slides)
            length = float(length)

            velocity = -1
            for point in timing_points:
                if time > point[0]:
                    velocity = point[1]
                    break

            slider_time += length / velocity * slides

            output.append((length * slides, velocity))

    return output, slider_time / total_time

def get_stats(input_file):
    with open(input_file, 'r', encoding='utf8') as fin:
        lines = fin.readlines()

    stats = {
        'HPDrainRate': -1,
        'CircleSize': -1,
        'OverallDifficulty': -1,
        'ApproachRate': -1,
        'Title': -2,
        'Artist': -2,
        'Creator': -2,
        'Version': -2,
    }

    for line in lines:
        for stat in stats:
            if line.startswith(stat + ':'):
                if stats[stat] == -1:
                    stats[stat] = float(line[line.index(':')+1:])
                else:
                    stats[stat] = line[line.index(':')+1:].strip()

    if stats['ApproachRate'] == -1:
        stats['ApproachRate'] = stats['OverallDifficulty']

    i = lines.index('[HitObjects]\n') + 1
    times = []
    while i < len(lines) and not lines[i].startswith('[') and lines[i].strip():
        ls = lines[i].split(',')
        times.append(int(ls[2]))
        i += 1
    length = (times[-1] - times[0]) // 1000

    return {
        'hp': stats['HPDrainRate'],
        'cs': stats['CircleSize'],
        'od': stats['OverallDifficulty'],
        'ar': stats['ApproachRate'],
        'title': stats['Title'],
        'artist': stats['Artist'],
        'creator': stats['Creator'],
        'version': stats['Version'],
        'length': length
    }

if __name__ == '__main__':
    print(get_stats(r"maps\Silentroom - Alt Futur (Riana) [Ultra].osu"))
    #get_sliders(r"maps\Silentroom - Alt Futur (Riana) [Ultra].osu", 'temp.txt')
    #graph_distribution(r"dists\Kano - Walk This Way! (Sotarks) [Ultra].osu.dist")
