import math

import calc
import getmaps
import getmedians

def manhattan(a, b):
    return sum(abs(a[i] - b[i]) for i in range(len(a)))

def euclidean(a, b):
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(len(a))))

def get_similar(map_id, n=50):
    medians = getmedians.get_medians()

    _, text = getmaps.get_map(map_id)
    with open('temp.txt', 'w', encoding='utf8', newline='') as f:
        f.write(text)
    median = getmedians.get_median(calc.get_distribution('temp.txt'))

    medians = list(medians.items())
    medians.sort(key=lambda m: manhattan(m[1], median))

    for i in range(n):
        print(medians[i])

if __name__ == '__main__':
    get_similar(1655981)
