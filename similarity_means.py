import math

import calc
import getmaps
import getmeans

def manhattan(a, b):
    return sum(abs(a[i] - b[i]) for i in range(len(a)))

def euclidean(a, b):
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(len(a))))

def get_similar(map_id, n=50):
    means = getmeans.get_means()

    _, text = getmaps.get_map(map_id)
    with open('temp.txt', 'w', encoding='utf8', newline='') as f:
        f.write(text)
    mean = getmeans.get_mean(calc.get_distribution('temp.txt'))

    means = list(means.items())
    means.sort(key=lambda m: manhattan(m[1], mean))

    for i in range(n):
        print(means[i])

if __name__ == '__main__':
    get_similar(2659369)
