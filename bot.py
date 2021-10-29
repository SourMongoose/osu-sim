# https://discord.com/api/oauth2/authorize?client_id=829860591405498419&permissions=18432&scope=bot

import asyncio
import discord
import math
import random
import time

import api
import similarity_buckets
import similarity_srs
import tokens

client = discord.Client()

async def send_error_message(ch, msg='Invalid input.'):
    color = discord.Color.from_rgb(255, 100, 100)
    embed = discord.Embed(description=msg, color=color)
    await ch.send(embed=embed)

def file_to_id(file):
    file_lower = file.replace('.dist', '').lower()
    if '.osu' not in file_lower:
        file_lower += '.osu'
    return map_ids.get(file_lower, None)

def file_to_link(file):
    id = file_to_id(file)
    return f'https://osu.ppy.sh/b/{id}' if id else ''

async def get_similar_maps(ch, map_id, page=1):
    perpage = 10
    n = page * perpage

    color = discord.Color.from_rgb(255, 255, 100)
    description = 'Calculating...'
    footer = 'This should take about 10 seconds.'
    embed = discord.Embed(description=description, color=color)
    embed.set_footer(text=footer)
    calc_msg = await ch.send(embed=embed)

    try:
        sim = similarity_buckets.get_similar(map_id, n)
    except:
        await calc_msg.delete()
        await send_error_message(ch)
        return

    if len(sim) < page * perpage:
        await calc_msg.delete()
        await send_error_message(ch, 'Not enough similar maps.')
        return

    color = discord.Color.from_rgb(100, 255, 100)
    title = f'Maps similar in structure to {map_id}:'
    description = '\n'.join(f'**{i+1})** {sim[i][0].replace(".osu.dist","")}\n{file_to_link(sim[i][0])}' for i in range((page-1)*perpage, page*perpage))
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text=f'Page {page} of 10')
    await calc_msg.edit(embed=embed)

async def get_rating_maps(ch, map_id, page=1, dt=False):
    perpage = 10
    n = page * perpage

    try:
        sim = similarity_srs.get_similar(map_id, n, dt)
    except:
        await send_error_message(ch)
        return

    color = discord.Color.from_rgb(100, 255, 100)
    title = f'Maps similar in star rating to {map_id}' + (' (+DT)' if dt else '') + ':'
    description = '\n'.join(f'**{i+1})** {sim[i][0].replace(".osu.dist","")}\n{file_to_link(sim[i][0])}' for i in range((page-1)*perpage, page*perpage))
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text=f'Page {page} of 10')
    await ch.send(embed=embed)

async def recommend_map(ch, username):
    if '(' in username:
        username = username[:username.index('(')].strip()

    api.refresh_token()
    try:
        user = api.get_user(username)
    except:
        await send_error_message(ch, f'User **{username}** not found.')
        return

    try:
        scores = api.get_scores(user['id'], limit=50)
        score_index = random.randrange(min(25, len(scores)))
        dt = 'DT' in scores[score_index]['mods'] or 'NC' in scores[score_index]['mods']
        sim = similarity_srs.get_similar(scores[score_index]['beatmap']['id'], 100, dt)
    except:
        await send_error_message(ch, f'Error fetching scores for user **{username}**. Please try again later.')
        return

    score_ids = set(score['beatmap']['id'] for score in scores)

    index = 0
    for i in range(len(sim)):
        map_id = file_to_id(sim[i][0])
        if int(map_id) in score_ids:
            continue
        if map_freq.get(map_id, 0) >= 150: # frequency threshold
            index = i
            if random.randrange(2):
                break

    color = discord.Color.from_rgb(100, 255, 100)
    modstr = ' +' + ''.join(scores[score_index]['mods']) if scores[score_index]['mods'] else ''
    description = f'**{sim[index][0]}**{modstr}\n{file_to_link(sim[index][0])}'
    embed = discord.Embed(description=description, color=color)
    embed.set_footer(text=f'Recommended map for {user["username"]}')
    await ch.send(embed=embed)

active_quizzes = {}
async def start_quiz(ch, au, params):
    if ch.id in active_quizzes:
        return

    active_quizzes[ch.id] = {}
    q = active_quizzes[ch.id]

    q['first'] = 'first' in params

    pool = []
    difficulties = []

    if 'topplays' in params:
        api.refresh_token()

        username = au.display_name
        if '(' in username:
            username = username[:username.index('(')].strip()

        try:
            user = api.get_user(username)
        except:
            await send_error_message(ch, f'User **{username}** not found.')
            return

        try:
            scores = api.get_scores(user['id'], limit=50, offset=0) + api.get_scores(user['id'], limit=50, offset=50)
        except:
            await send_error_message(ch, f'Error fetching scores for user **{username}**. Please try again later.')
            return

        score_ids = list(set(score['beatmap']['beatmapset_id'] for score in scores))

        pool.extend(score_ids)
        difficulties.append('Top plays')
    else:
        if 'easy' in params:
            pool.extend(easy)
            difficulties.append('Easy')
        if 'medium' in params:
            pool.extend(medium)
            difficulties.append('Medium')
        if 'hard' in params:
            pool.extend(hard)
            difficulties.append('Hard')
        if 'impossible' in params:
            pool.extend(impossible)
            difficulties.append('Impossible')
        if 'iceberg' in params:
            pool.extend(iceberg)
            difficulties.append('Iceberg')

    if not pool:
        pool = easy
        difficulties = ['Easy']

    mapset_ids = []
    while len(mapset_ids) < 10:
        selected = pool[random.randrange(len(pool))]
        if selected not in mapset_ids:
            mapset_ids.append(selected)

    api.refresh_token()
    mapset_infos = []
    i = 0
    while i < len(mapset_ids):
        try:
            mapset_infos.append(api.get_beatmapset(mapset_ids[i]))
            i += 1
        except:
            continue

    answers = []
    images = []
    for mi in mapset_infos:
        name = mi['title']
        namesplit = name.split(' ')
        for i in range(1, len(namesplit)):
            if any(namesplit[i].startswith(c) for c in '~([-<') \
                    or any(alphanumeric(namesplit[i].lower()) == s for s in ['ft', 'feat', 'featuring']) \
                    or any(namesplit[i].lower().startswith(s) for s in ['ft.', 'feat.', 'featuring.']) \
                    or 'tv' in namesplit[i].lower():
                name = ''.join(namesplit[:i])
                break
        answers.append(alphanumeric(name.lower()))

        images.append(mi['covers']['cover'])

    q['answers'] = answers
    q['scores'] = {}

    guess_time = 10

    await ch.send('Welcome to the osu! beatmap quiz! You will be given a series of beatmap backgrounds; try to type '
                  'the title of the beatmap as quickly as possible.\n\n'
                  f"Current settings: {'+'.join(difficulties)}, 10 songs, {guess_time}s guess time, {'first-guess' if q['first'] else 'time-based'} scoring\n\n"
                  'First background will appear in 5 seconds!')

    await asyncio.sleep(5)

    if ch.id not in active_quizzes:
        return

    for i in range(len(answers)):
        q['index'] = i
        q['window'] = (time.time(), time.time() + guess_time)
        q['curr_scores'] = {}

        await ch.send(images[i])

        if q['first']:
            for _ in range(guess_time):
                if q['curr_scores']:
                    break
                await asyncio.sleep(1)
        else:
            await asyncio.sleep(guess_time)

        if ch.id not in active_quizzes:
            return

        output = f"The answer was: {mapset_infos[i]['title']}\n"
        if q['curr_scores']:
            output += '\n' + '\n'.join(f"{au.display_name}: {q['curr_scores'][au]}" for au in q['curr_scores']) + '\n'
        if i < len(answers) - 1:
            output += '\nNext question in 5 seconds.\n'
        output += '-' * 20
        await ch.send(output)

        for au in q['curr_scores']:
            if au not in q['scores']:
                q['scores'][au] = 0
            q['scores'][au] += q['curr_scores'][au]

        if i < len(answers) - 1:
            await asyncio.sleep(5)

        if ch.id not in active_quizzes:
            return

    scores = list(q['scores'].items())
    scores.sort(key=lambda s: -s[1])
    output = 'Final standings:\n'
    icons = {
        0: ':first_place:',
        1: ':second_place:',
        2: ':third_place:'
    }
    output += '\n'.join(f"{icons.get(i, '')}{scores[i][0].display_name}: {scores[i][1]}" for i in range(len(scores)))
    await ch.send(output)

    active_quizzes.pop(ch.id)

async def quiz_guess(au, ch, msg):
    q = active_quizzes[ch.id]

    t = time.time()
    w = q['window']
    if lerp(w[0], w[1], t) > 1:
        return

    guess = alphanumeric(msg.lower())

    if q['answers'][q['index']] not in guess:
        return

    if q['first'] and q['curr_scores'] or au in q['curr_scores']:
        return

    score = 1 if q['first'] else 5 - math.floor(lerp(w[0], w[1], t) / 0.2)
    q['curr_scores'][au] = score

def lerp(a, b, x):
    return (x - a) / (b - a)

def alphanumeric(s):
    output = ''
    for c in s:
        if '0' <= c <= '9' or 'a' <= c <= 'z':
            output += c
    return output

def get_map_ids():
    map_ids = {}

    with open('filenames.txt', 'r') as f:
        lines = f.readlines()

    for i in range(0, len(lines), 2):
        map_ids[lines[i + 1].strip().lower()] = lines[i].strip()

    return map_ids

def get_map_freq(filename='mapfreq.txt'):
    map_freq = {}

    with open(filename, 'r') as f:
        lines = f.readlines()

    for line in lines:
        id, freq = line.split(',')
        map_freq[id] = int(freq)

    return map_freq

def get_mapsets(filename='setids_country.txt'):
    mapsets = []

    with open(filename, 'r') as f:
        lines = f.readlines()

    for line in lines:
        ls = line.strip().split(',')
        mapsets.append((int(ls[0]), int(ls[1])))

    mapsets.sort(key=lambda t: -t[1])

    return mapsets

map_ids = get_map_ids()
map_freq = get_map_freq()
map_freq_country = get_map_freq('mapfreq_country.txt')

# get mapsets for beatmap quiz
mapsets = get_mapsets()
easy = []
medium = []
hard = []
impossible = []
iceberg = []
for i in range(len(mapsets)):
    if i < 1000:
        easy.append(mapsets[i][0])
    elif i < 3000:
        medium.append(mapsets[i][0])
    elif i < 5000:
        hard.append(mapsets[i][0])
    elif i > len(mapsets) - 1000:
        iceberg.append(mapsets[i][0])
    else:
        impossible.append(mapsets[i][0])

# command starter
C = '.'

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name=C+'help'))
    print('When you see it!')

@client.event
async def on_message(message):
    msg = message.content.lower()
    ch = message.channel
    au = message.author

    # ignore bot messages
    if au.bot:
        return

    # help command
    if msg == C+'help' or msg == C+'h':
        title = 'Command List'
        color = discord.Color.from_rgb(150,150,150)
        description = f'**{C}s**im `<beatmap id/link>` `[<page>]`\nFind similar maps (based on map structure)\n\n' \
                      f'**{C}sr** `<beatmap id/link>` `[dt]` `[<page>]`\nFind similar maps (based on star rating)\n\n' \
                      f'**{C}r**ec `[<username/id>]`\nRecommend a map\n\n' \
                      f'**{C}q**uiz `[easy/medium/hard/impossible]` `[first]`\nStart the beatmap quiz\n\n' \
                      f'**{C}i**nvite\nGet this bot\'s invite link\n\n' \
                      f'**{C}h**elp\nView commands'
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text="Omit brackets. Square brackets ([]) indicate optional parameters.")
        await ch.send(embed=embed)

    # invite link
    if msg == C+'invite' or msg == C+'i':
        title = 'Invite this bot to your server:'
        color = discord.Color.from_rgb(150, 150, 150)
        description = 'https://discord.com/api/oauth2/authorize?client_id=829860591405498419&permissions=18432&scope=bot'
        embed = discord.Embed(title=title, description=description, color=color)
        await ch.send(embed=embed)

    # find similar maps (map structure)
    if any(msg.startswith(C + s + ' ') for s in ['s', 'sim', 'similar']):
        msg = msg[msg.index(' ')+1:]

        # parse input
        try:
            map_id = msg[:msg.index(' ')] if ' ' in msg else msg
            if '/' in map_id:
                map_id = map_id[map_id.strip('/').rindex('/')+1:]
            map_id = ''.join(c for c in map_id if '0' <= c <= '9')

            page = 1
            if ' ' in msg:
                page = int(msg[msg.index(' ')+1:])

            if not (1 <= page <= 10):
                raise Exception

            await get_similar_maps(ch, map_id, page)
        except:
            await send_error_message(ch)

    # find similar maps (star rating)
    if msg.startswith(C + 'sr '):
        msg = msg[msg.index(' ') + 1:]
        args = msg.split(' ')

        # parse input
        try:
            map_id = args[0]
            if '/' in map_id:
                map_id = map_id[map_id.strip('/').rindex('/') + 1:]
            map_id = ''.join(c for c in map_id if '0' <= c <= '9')

            dt = 'dt' in args

            page = 1
            for p in range(1, 11):
                if str(p) in args:
                    page = p
                    break

            await get_rating_maps(ch, map_id, page, dt)
        except:
            await send_error_message(ch)

    # recommend a map
    if any(msg.startswith(C + s) for s in ['r', 'rec']):
        if msg == C + 'r' or msg == C + 'rec':
            username = au.display_name
        elif any(msg.startswith(C + s + ' ') for s in ['r', 'rec']):
            username = msg[msg.index(' ') + 1:]
        else:
            return

        await recommend_map(ch, username)

    # beatmap bg trivia
    if any(msg.startswith(C + s) for s in ['q', 'quiz']) \
            and not any(msg.startswith(C + s) for s in ['q abort', 'quiz abort']):
        if ' ' in msg:
            await start_quiz(ch, au, msg[msg.index(' ') + 1:])
        else:
            await start_quiz(ch, au, '')
    if ch.id in active_quizzes:
        if any(msg.startswith(C + s) for s in ['q abort', 'quiz abort']):
            active_quizzes.pop(ch.id)
            await ch.send('Quiz has been aborted.')
        else:
            await quiz_guess(au, ch, msg)

client.run(tokens.token)
