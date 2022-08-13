import json
import numpy as np

import api

def estimate_score(id, pp):
    if id not in scores:
        return None
    scores_sorted = sorted(scores[id], key=lambda sc: abs(sc[0] - pp))
    cutoff = 0
    while cutoff < len(scores_sorted) and abs(scores_sorted[cutoff][0] - pp) < pp / 5:
        cutoff += 1
    if cutoff < 10:
        return None

    scores_sorted = scores_sorted[:cutoff]
    x = [sc[0] for sc in scores_sorted]
    y = [userids[sc[1]]['rank'] for sc in scores_sorted]
    coeffs = np.polyfit(x, y, 2)
    poly_fn = np.poly1d(coeffs)

    return round(poly_fn(pp))

def score_string(score):
    s = f"[{score['beatmapset']['artist']} - {score['beatmapset']['title']} [{score['beatmap']['version']}]](https://osu.ppy.sh/b/{score['beatmap']['id']})"
    modstr = (' +' + ''.join(m for m in score['mods'])) if score['mods'] else ''
    return f"{s}{modstr} ({round(score['pp'])}pp)"

def get_rank_estimate(user):
    api.refresh_token()

    fail = 0
    m = None
    while fail < 5:
        try:
            top50 = api.get_scores(user, limit=50, offset=0)
            top100 = api.get_scores(user, limit=50, offset=50)

            m = top50 + top100
            break
        except:
            fail += 1

    if fail >= 5:
        return None

    estimates = []
    for score in m:
        est = estimate_score(str(score['beatmap']['id']), score['pp'])
        if est:
            estimates.append((score_string(score), est))

    estimates.sort(key=lambda e: e[1])

    weights = [.95**i for i in range(len(estimates))]
    estimated_rank = sum(estimates[i][1] * weights[i] for i in range(len(estimates))) / sum(weights)

    return estimated_rank, estimates[:10]

with open('ids_country.json', 'r') as f:
    userids = json.load(f)

scores = {}
try:
    with open('mapids_pp.json', 'r') as f:
        scores = json.load(f)
except:
    with open('mapids_pp.txt') as f:
        lines = f.readlines()
    for line in lines:
        id, idx, uid, mods, pp = line.split(',')
        if id not in scores:
            scores[id] = []
        scores[id].append((float(pp), uid))
    with open('mapids_pp.json', 'w') as f:
        json.dump(scores, f)

if __name__ == '__main__':
    est = get_rank_estimate(13269506)
    print(f'Estimated rank: #{round(est[0])}\n')
    print('rank | score\n----------------------')
    for sc in est[1]:
        print(f'{sc[1]} | {sc[0]}')
