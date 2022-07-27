import math
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d

def angle_between(x1, y1, x2, y2, x3, y3):
    a1 = math.atan2(y1 - y2, x1 - x2) * 180 / math.pi
    a2 = math.atan2(y3 - y2, x3 - x2) * 180 / math.pi
    diff = abs(a2 - a1)
    return min(diff, 360 - diff)

def distance_between(x1, y1, x2, y2):
    return math.sqrt((y2 - y1) * (y2 - y1) + (x2 - x1) * (x2 - x1))

def get_distribution(input_file, output_file=None):
    if output_file is None:
        output_file = input_file + '.dist'

    with open(input_file, 'r', encoding='utf8') as fin:
        lines = fin.readlines()

    with open(output_file, 'w') as fout:
        i = lines.index('[HitObjects]\n') + 1
        qx = qy = qt = zx = zy = zt = -1
        while i < len(lines):
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
                fout.write(f'{angle},{time},{dist}\n')

            qx, qy, qt = zx, zy, zt
            zx, zy, zt = x, y, t

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

def get_sliders(input_file, output_file=None):
    if output_file is None:
        output_file = input_file + '.sldr'

    with open(input_file, 'r', encoding='utf8') as fin:
        lines = fin.readlines()

    slider_mult = -1
    for line in lines:
        if line.startswith('SliderMultiplier'):
            slider_mult = float(line[line.index(':') + 1:]) * 100
            break

    beat_length = -1
    timing_points = []
    i = lines.index('[TimingPoints]\n') + 1
    while i < len(lines) and not lines[i].startswith('[') and lines[i].strip():
        ls = lines[i].split(',')
        while len(ls) < 8:
            ls.append(0)

        time, beatLength, meter, sampleSet, sampleIndex, volume, uninherited, effects = (float(x) for x in ls)

        if uninherited:
            beat_length = beatLength
            timing_points.append((time, slider_mult / beat_length))
        else:
            timing_points.append((time, slider_mult / beat_length * (-100 / beatLength)))

        i += 1

    timing_points[0] = (0, timing_points[0][1])
    timing_points = timing_points[::-1]

    with open(output_file, 'w') as fout:
        slider_time = 0
        total_time = 0
        first_object = -1

        i = lines.index('[HitObjects]\n') + 1
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

                velocity = -1
                for point in timing_points:
                    if float(time) > point[0]:
                        velocity = point[1]
                        break

                slider_time += float(length) / velocity

                fout.write(f'{length.strip()}, {velocity}\n')

        fout.write(f'{slider_time / total_time}\n')

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
    }

    for line in lines:
        for stat in stats:
            if line.startswith(stat):
                stats[stat] = float(line[line.index(':')+1:])

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
        'length': length
    }

if __name__ == '__main__':
    print(get_stats(r"maps\Silentroom - Alt Futur (Riana) [Ultra].osu"))
    #get_sliders(r"maps\Silentroom - Alt Futur (Riana) [Ultra].osu", 'temp.txt')
    #graph_distribution(r"dists\Kano - Walk This Way! (Sotarks) [Ultra].osu.dist")
