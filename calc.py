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

if __name__ == '__main__':
    graph_distribution(r"dists\Mitsuki Nakae - Ouka Enbu (Lasse) [Petal].osu.dist")
