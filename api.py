import requests
import time

from secret import *

token = ''

def get_access_token():
    params = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
        'scope': 'public',
    }

    r = requests.post('https://osu.ppy.sh/oauth/token', data=params, timeout=1)

    return r.json()

def write_new_token():
    token = get_access_token()
    with open('token.txt', 'w') as f:
        f.write(str(int(time.time() + token['expires_in'])) + '\n')  # expiration time
        f.write(token['access_token'] + '\n')

def refresh_token():
    # get token
    try:
        with open('token.txt', 'r') as f:
            exp = int(f.readline().strip())
        if time.time() > exp:
            write_new_token()
    except:
        write_new_token()

    with open('token.txt', 'r') as f:
        f.readline()
        global token
        token = f.readline().strip()

def get_rankings(mode='osu', type='performance', page=None, country=None):
    params = {}
    if page is not None: params['page'] = page
    if country is not None: params['country'] = country

    headers = {'Authorization': f'Bearer {token}'}

    r = requests.get(f'https://osu.ppy.sh/api/v2/rankings/{mode}/{type}', params=params, headers=headers, timeout=1)

    return r.json()

def get_user(username):
    headers = {'Authorization': f'Bearer {token}'}

    r = requests.get(f'https://osu.ppy.sh/api/v2/users/{username}', headers=headers, timeout=1)

    return r.json()

def get_scores(user, type='best', include_fails=None, mode='osu', limit=None, offset=None):
    params = {}
    if include_fails is not None: params['include_fails'] = include_fails
    if mode is not None: params['mode'] = mode
    if limit is not None: params['limit'] = limit
    if offset is not None: params['offset'] = offset

    headers = {'Authorization': f'Bearer {token}'}

    r = requests.get(f'https://osu.ppy.sh/api/v2/users/{user}/scores/{type}', params=params, headers=headers, timeout=1)

    return r.json()

def get_favorites(user, limit=None, offset=None):
    params = {}
    if limit is not None: params['limit'] = limit
    if offset is not None: params['offset'] = offset

    headers = {'Authorization': f'Bearer {token}'}

    r = requests.get(f'https://osu.ppy.sh/api/v2/users/{user}/beatmapsets/favourite', params=params, headers=headers, timeout=1)

    return r.json()

def get_beatmap(id):
    headers = {'Authorization': f'Bearer {token}'}

    r = requests.get(f'https://osu.ppy.sh/api/v2/beatmaps/{id}', headers=headers, timeout=1)

    return r.json()

def calculate_sr(id, mods=[]):
    params = {
        'Map': str(id),
        'Mods': mods,
    }

    r = requests.post('https://newpp.stanr.info/api/maps/calculate', json=params, timeout=5)

    return r.json()
