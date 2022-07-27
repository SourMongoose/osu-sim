# https://discord.com/api/oauth2/authorize?client_id=829860591405498419&permissions=18432&scope=bot

import asyncio
import discord
import math
import random
import time
import traceback

import api
import findppmaps
import similarity_buckets
import similarity_sliders
import similarity_srs
import tokens

# debugging
DEBUG = False

client = discord.Client()

async def send_error_message(ch, msg='Invalid input.'):
    color = discord.Color.from_rgb(255, 100, 100)
    embed = discord.Embed(description=msg, color=color)
    await ch.send(embed=embed)

def file_to_id(file):
    file_lower = file.replace('.dist', '').replace('.sldr', '').lower()
    if '.osu' not in file_lower:
        file_lower += '.osu'
    return map_ids.get(file_lower, None)

def id_to_file(id):
    filename = filenames.get(id, None)
    return filename.replace('.osu', '') if filename else None

def file_to_link(file):
    id = file_to_id(file)
    return f'https://osu.ppy.sh/b/{id}' if id else ''

async def get_similar_maps(ch, map_id, page=1, filters=None):
    perpage = 10
    n = page * perpage

    color = discord.Color.from_rgb(255, 255, 100)
    description = 'Calculating...'
    footer = 'This should take about 10 seconds.'
    embed = discord.Embed(description=description, color=color)
    embed.set_footer(text=footer)
    calc_msg = await ch.send(embed=embed)

    try:
        sim = similarity_buckets.get_similar(map_id, n, filters)
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
    description = '\n'.join(f'**{i+1})** [{sim[i][0].replace(".osu.dist","")}]({file_to_link(sim[i][0])})' for i in range((page-1)*perpage, page*perpage))
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text=f'Page {page} of 10')
    await calc_msg.edit(embed=embed)

async def get_rating_maps(ch, map_id, page=1, dt=False):
    perpage = 10
    n = page * perpage

    try:
        sim = similarity_srs.get_similar(map_id, n, ['DT'] if dt else [])
    except:
        await send_error_message(ch)
        return

    if not sim:
        await send_error_message(ch, 'Map not found in local database.')
        return

    color = discord.Color.from_rgb(100, 255, 100)
    title = f'Maps similar in star rating to {map_id}' + (' (+DT)' if dt else '') + ':'
    description = '\n'.join(f'**{i+1})** [{sim[i][0].replace(".osu.dist","")}]({file_to_link(sim[i][0])})' for i in range((page-1)*perpage, page*perpage))
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text=f'Page {page} of 10')
    await ch.send(embed=embed)

async def get_slider_maps(ch, map_id, page=1):
    perpage = 10
    n = page * perpage

    color = discord.Color.from_rgb(255, 255, 100)
    description = 'Calculating...'
    footer = 'This should take about 10 seconds.'
    embed = discord.Embed(description=description, color=color)
    embed.set_footer(text=footer)
    calc_msg = await ch.send(embed=embed)

    try:
        sim = similarity_sliders.get_similar(map_id, n)
    except:
        await calc_msg.delete()
        await send_error_message(ch)
        return

    if len(sim) < page * perpage:
        await calc_msg.delete()
        await send_error_message(ch, 'Not enough similar maps.')
        return

    color = discord.Color.from_rgb(100, 255, 100)
    title = f'Maps similar in sliders to {map_id}:'
    description = '\n'.join(f'**{i+1})** [{sim[i][0].replace(".osu.sldr","")}]({file_to_link(sim[i][0])})' for i in range((page-1)*perpage, page*perpage))
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text=f'Page {page} of 10')
    await calc_msg.edit(embed=embed)

async def get_pp_maps(ch, min_pp=0., max_pp=2e9, mods_include='', mods_exclude='', page=1):
    perpage = 10
    n = page * perpage

    try:
        mods_include, mods_exclude = findppmaps.simplify_mods(mods_include), findppmaps.simplify_mods(mods_exclude)
        maps = findppmaps.find_pp_maps(min_pp, max_pp, mods_include, mods_exclude, limit=n)
    except:
        await send_error_message(ch)
        return

    if len(maps) < n:
        await send_error_message(ch, 'Not enough maps.')
        return

    color = discord.Color.from_rgb(100, 255, 100)
    title = f'Overweight maps from {min_pp}-{max_pp}pp'
    if mods_include:
        title += f', using mods {mods_include}'
    if mods_exclude:
        title += f', excluding mods {mods_exclude}'
    title += ':'
    modcombo = lambda i: f' +{maps[i][1]}' if maps[i][1] else ''
    description = '\n'.join(f'**{i + 1})** [{id_to_file(maps[i][0])}](https://osu.ppy.sh/b/{maps[i][0]}){modcombo(i)}' for i in
                            range((page - 1) * perpage, page * perpage))
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text=f'Page {page} of 10')
    await ch.send(embed=embed)

async def recommend_map(ch, username):
    if '(' in username:
        username = username[:username.index('(')].strip()

    api.refresh_token()

    counter = 0
    user = None
    while counter < 3:
        try:
            user = api.get_user(username)
            break
        except:
            counter += 1

    if not user:
        await send_error_message(ch, f'User **{username}** not found.')
        return

    scores = None
    while counter < 3:
        try:
            scores = api.get_scores(user['id'], limit=50)
            break
        except:
            counter += 1

    if not scores:
        await send_error_message(ch, f'Error fetching scores for user **{username}**. Please try again later.')
        return

    counter = 0
    score_index = 0
    sim = None
    while counter < 5:
        score_index = random.randrange(min(25, len(scores)))
        sim = similarity_srs.get_similar(scores[score_index]['beatmap']['id'], 100, scores[score_index]['mods'])
        if sim:
            break

        counter += 1

    if not sim:
        await send_error_message(ch, f'Error finding map recommendations for user **{username}**. Please try again later.')
        return

    score_ids = set(score['beatmap']['id'] for score in scores)

    farm_maps = []
    for i in range(len(sim)):
        map_id = file_to_id(sim[i][0])
        if not map_id or int(map_id) in score_ids:
            continue
        # if map_freq.get(map_id, 0) >= 150: # frequency threshold
        #     farm_maps.append(i)

        # calculate overweightedness
        mapinfo = findppmaps.get_map_info(map_id, ''.join(m for m in scores[score_index]['mods']))
        ow = findppmaps.overweight(mapinfo) if mapinfo else 0
        if ow > 0.15: # threshold
            farm_maps.append(i)

    if not farm_maps:
        index = 0
    else:
        index = farm_maps[random.randrange(0, min(len(farm_maps), 50))]

    color = discord.Color.from_rgb(100, 255, 100)
    modstr = ' +' + ''.join(scores[score_index]['mods']) if scores[score_index]['mods'] else ''
    description = f'**{sim[index][0]}**{modstr}\n{file_to_link(sim[index][0])}'
    embed = discord.Embed(description=description, color=color)
    embed.set_footer(text=f'Recommended map for {user["username"]}')
    await ch.send(embed=embed)

async def get_farmer_rating(ch, username):
    if '(' in username:
        username = username[:username.index('(')].strip()

    api.refresh_token()

    counter = 0
    user = None
    while counter < 3:
        try:
            user = api.get_user(username)
            break
        except:
            counter += 1

    if not user:
        await send_error_message(ch, f'User **{username}** not found.')
        return

    scores = None
    while counter < 3:
        try:
            scores = api.get_scores(user['id'], limit=50) + api.get_scores(user['id'], limit=50, offset=50)
            break
        except:
            counter += 1

    if not scores:
        await send_error_message(ch, f'Error fetching scores for user **{username}**. Please try again later.')
        return

    farm_ratings = []
    for i in range(len(scores)):
        score = scores[i]
        map_info = findppmaps.get_map_info(str(score['beatmap']['id']), ''.join(m for m in score['mods']))
        if map_info:
            s = f"{score['beatmapset']['artist']} - {score['beatmapset']['title']} [{score['beatmap']['version']}]"
            modstr = (' +' + ''.join(m for m in score['mods'])) if score['mods'] else ''
            farm_ratings.append((
                f"[{s}](https://osu.ppy.sh/b/{score['beatmap']['id']}){modstr} ({round(score['pp'])}pp)",
                findppmaps.overweight_raw(map_info) * 100,
                0.95 ** i
            ))

    farm_ratings.sort(key=lambda f: f[1])
    overall = round(sum(f[1] * f[2] for f in farm_ratings) / sum(f[2] for f in farm_ratings), 2)

    color = discord.Color.from_rgb(100, 255, 100)
    title = f'Farmer rating for {username}:'
    description = f'**{overall}**\n\n**Most farm plays:**\n' + '\n'.join(f'**{round(f[1], 2):.2f}** | {f[0]}' for f in farm_ratings[-5:][::-1]) \
            + '\n\n**Least farm plays:**\n' + '\n'.join(f'**{round(f[1], 2):.2f}** | {f[0]}' for f in farm_ratings[:10])
    embed = discord.Embed(title=title, description=description, color=color)
    await ch.send(embed=embed)

async def chez(message):
    embeds = message.embeds
    if not embeds:
        return

    embed = embeds[0].to_dict()
    if 'author' in embed and 'chezbananas on' in embed['author']['name']:
        map_url = embed['author']['url']
        map_id = map_url[map_url.rindex('/') + 1:]
        api.refresh_token()
        map_details = api.get_beatmap(map_id)
        map_title = map_details['beatmapset']['title']
        map_status = map_details['beatmapset']['status']
        lines = embed['description'].split('\n')
        mods = lines[0][lines[0].index('`') + 1:]
        mods = mods[:mods.index('`')]
        acc = lines[1][lines[1].rindex(' ') + 1:]
        misscount = lines[2][lines[2].rindex('/') + 1:-1]

        pastas = []
        if mods == 'HD':
            pastas.append(
                f'After plowing its way through to the quarterfinals, Berkeley Team A was put up against '
                f'Stanford University, who proved challenging for them with an especially strong player: '
                f'"chezbananas". "chezbananas" is notorious for their strength in "HD," or "Hidden" — one of '
                f'the osu! game modifiers that remove hit objects after they appear, increasing the game\'s '
                f'difficulty.')
        if 'FC' in lines[1] or misscount != '0':
            pastas.append(
                f"I mean if you go and >rs {map_title} then what do you expect? It has such a big status as a "
                f"chezbananas score that you can't avoid being >c'd. In my honest opinion there are maps that "
                f"are tied to such grand scores that they should be given a status where they are not allowed "
                f"to be >rs'd if chezbananas has a better score ({map_title} being one of them). That being said "
                f"I haven't looked at the map so I have no opinion on it, because the quality of the map is "
                f"irrelevant in this matter. This is about preserving history of osu! and therefore I hope that "
                f"this doesn't become a trend in the future.")
        else:
            pastas.append(
                f"chezbananas's {map_title} {mods} {acc} full combo. Without a doubt, one of the most "
                f"impressive plays ever set in osu! history, but one that takes some experience to "
                f"appreciate fully. In the years that this map has been {map_status}, chezbananas's score "
                f"remains the ONLY {mods.upper()} FC, and there's much more to unpack about this score. "
                f"While some maps easily convey how difficult they are through the raw aim, or speed "
                f"requirements, {map_title} is much more nuanced than it may seem at first glance.")

        if pastas:
            await message.channel.send(random.choice(pastas))
    elif 'author' in embed and 'Azurium on MATZcore [Lolicore]' in embed['author']['name']:
        await message.channel.send('shat on')

active_quizzes = {}
async def start_quiz(ch, au, params):
    if ch.id in active_quizzes:
        return

    active_quizzes[ch.id] = {}
    q = active_quizzes[ch.id]

    q['first'] = 'first' in params
    q['diff'] = 'diff' in params

    pool = []
    difficulties = []
    if q['diff']:
        easy, medium, hard, impossible, iceberg = easy_diffs, medium_diffs, hard_diffs, impossible_diffs, iceberg_diffs
    else:
        easy, medium, hard, impossible, iceberg = easy_sets, medium_sets, hard_sets, impossible_sets, iceberg_sets

    if 'topplays' in params and not q['diff']:
        usernames = None

        i = params.index('topplays')
        if i + 8 < len(params):
            bracket = params[i + 8]
            brackets = {
                '(': ')',
                '[': ']',
                '{': '}'
            }
            if bracket in brackets:
                usernames = params[i + 9:]
                if brackets[bracket] not in usernames:
                    active_quizzes.pop(ch.id)
                    return
                usernames = usernames[:usernames.index(brackets[bracket])].split(',')
                for i in range(len(usernames)):
                    usernames[i] = usernames[i].strip()

        api.refresh_token()

        if not usernames:
            username = au.display_name
            if '(' in username:
                username = username[:username.index('(')].strip()
            usernames = [username]

        users = []
        for username in usernames:
            try:
                user = api.get_user(username)
                users.append(user)
            except:
                await send_error_message(ch, f'User **{username}** not found.')
                active_quizzes.pop(ch.id)
                return

        for i in range(len(users)):
            user = users[i]
            try:
                scores = api.get_scores(user['id'], limit=50, offset=0) + api.get_scores(user['id'], limit=50, offset=50)
            except:
                await send_error_message(ch, f'Error fetching scores for user **{usernames[i]}**. Please try again later.')
                active_quizzes.pop(ch.id)
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
            if q['diff']:
                mapset_infos.append(api.get_beatmap(mapset_ids[i]))
            else:
                mapset_infos.append(api.get_beatmapset(mapset_ids[i]))

            i += 1
        except:
            continue

    answers = []
    images = []
    for mi in mapset_infos:
        name = mi['beatmapset']['title'] if q['diff'] else mi['title']
        namesplit = name.split(' ')
        for i in range(1, len(namesplit)):
            if any(namesplit[i].startswith(c) for c in '~([-<') \
                    or any(alphanumeric(namesplit[i].lower()) == s for s in ['ft', 'feat', 'featuring']) \
                    or any(namesplit[i].lower().startswith(s) for s in ['ft.', 'feat.', 'featuring.']) \
                    or 'tv' in namesplit[i].lower():
                name = ''.join(namesplit[:i])
                break
            if any(c in namesplit[i] for c in '~([<'):
                for c in '~([<':
                    if c in namesplit[i]:
                        namesplit[i] = namesplit[i][:namesplit[i].index(c)]
                name = ''.join(namesplit[:i + 1])
                break
        answers.append(alphanumeric(name.lower()))

        images.append(f'**[{mi["version"]}]**' if q['diff'] else mi['covers']['cover'])

    q['answers'] = answers
    q['scores'] = {}

    guess_time = 10

    if q['diff']:
        await ch.send(
            'Welcome to the osu! beatmap quiz! You will be given a series of difficulty names; try to type '
            'the title of the beatmap as quickly as possible.\n\n'
            f"Current settings: {'+'.join(difficulties)}, 10 songs, {guess_time}s guess time, {'first-guess' if q['first'] else 'time-based'} scoring\n\n"
            'First difficulty name will appear in 5 seconds!')
    else:
        await ch.send(
            'Welcome to the osu! beatmap quiz! You will be given a series of beatmap backgrounds; try to type '
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

        output = f"The answer was: {mapset_infos[i]['beatmapset']['title'] if q['diff'] else mapset_infos[i]['title']}\n"
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
    if 'window' not in q:
        return
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

def get_filenames():
    filenames = {}

    with open('filenames.txt', 'r') as f:
        lines = f.readlines()

    for i in range(0, len(lines), 2):
        filenames[lines[i].strip()] = lines[i + 1].strip()

    return filenames

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

def get_unique_diffnames(filename='filenames.txt'):
    diffnames = {}
    diffname_set = set()
    diffname_dupes = set()

    with open(filename, 'r') as f:
        lines = f.readlines()

    for i in range(0, len(lines), 2):
        filename = lines[i + 1].strip()
        try:
            diffname = filename[filename.rindex(') [') + 3:-5]
        except:
            continue

        if any(x in diffname.lower() for x in ['beginner', 'easy', 'normal', 'hard', 'hyper', 'insane', 'extra', 'expert', 'extreme', 'another', 'lunatic']):
            continue

        diffnames[lines[i].strip()] = diffname
        if diffname.lower() in diffname_set:
            diffname_dupes.add(diffname.lower())
        else:
            diffname_set.add(diffname.lower())

    # remove duplicates
    for id in list(diffnames.keys()):
        if diffnames[id].lower() in diffname_dupes:
            diffnames.pop(id)

    return diffnames

map_ids = get_map_ids()
filenames = get_filenames()
map_freq = get_map_freq()
map_freq_country = get_map_freq('mapfreq_country.txt')

# get mapsets for beatmap quiz
mapsets = get_mapsets()
easy_sets = []
medium_sets = []
hard_sets = []
impossible_sets = []
iceberg_sets = []
for i in range(len(mapsets)):
    if i < 1000:
        easy_sets.append(mapsets[i][0])
    elif i < 3000:
        medium_sets.append(mapsets[i][0])
    elif i < 5000:
        hard_sets.append(mapsets[i][0])
    elif i > len(mapsets) - 1000:
        iceberg_sets.append(mapsets[i][0])
    else:
        impossible_sets.append(mapsets[i][0])

# get difficulty names for beatmap quiz
diffnames = get_unique_diffnames('filenames.txt')
diff_freq = []
for id in map_freq_country:
    if id in diffnames:
        diff_freq.append((id, map_freq_country[id]))
diff_freq.sort(key=lambda t: -t[1])
easy_diffs = []
medium_diffs = []
hard_diffs = []
impossible_diffs = []
iceberg_diffs = []
for i in range(len(diff_freq)):
    if i < 500:
        easy_diffs.append(diff_freq[i][0])
    elif i < 1500:
        medium_diffs.append(diff_freq[i][0])
    elif i < 2500:
        hard_diffs.append(diff_freq[i][0])
    elif i > len(diff_freq) - 500:
        iceberg_diffs.append(diff_freq[i][0])
    else:
        impossible_diffs.append(diff_freq[i][0])

# command starter
C = ',' if DEBUG else '.'

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name=C+'help'))
    print('When you see it!')

@client.event
async def on_message(message):
    msg = message.content.lower()
    ch = message.channel
    au = message.author

    # chez >c
    if au.id == 289066747443675143:
        await chez(message)

    # ignore other bot messages
    if au.bot:
        return

    # help command
    if msg == C+'help' or msg == C+'h':
        title = 'Command List'
        color = discord.Color.from_rgb(150,150,150)
        description = f'**{C}s**im `<beatmap id/link>` `[<filters>]` `[<page>]`\nFind similar maps (based on map structure)\n\n' \
                      f'**{C}sr** `<beatmap id/link>` `[dt]` `[<page>]`\nFind similar maps (based on star rating)\n\n' \
                      f'**{C}sl**ider `<beatmap id/link>` `[<page>]`\nFind similar maps (based on sliders)\n\n' \
                      f'**{C}pp** `<min>-<max>` `[-][<mods>]` `[<page>]`\nFind overweighted maps\n\n' \
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
        params = msg.split(' ')
        try:
            map_id = params[0]
            if '/' in map_id:
                map_id = map_id[map_id.strip('/').rindex('/')+1:]
            map_id = ''.join(c for c in map_id if '0' <= c <= '9')

            page = 1

            if len(params) > 1:
                for param in params[1:]:
                    if param.isnumeric():
                        page = int(param)
                        break

                symbols = ['!=', '>=', '<=', '>', '<', '=']
                supported_filters = ['ar', 'od', 'hp', 'cs', 'length']
                filters = []
                for param in params[1:]:
                    for symbol in symbols:
                        if symbol in param:
                            filter_key = param[:param.index(symbol)]
                            filter_value = float(param[param.index(symbol)+len(symbol):])
                            if filter_key in supported_filters:
                                filters.append((filter_key, symbol, filter_value))
                            else:
                                if filter_key:
                                    await send_error_message(ch, f'Filter `{filter_key}` not currently supported.')
                                else:
                                    await send_error_message(ch, "Don't include spaces when using filters (e.g. `ar<9` instead of `ar < 9`)")
                                return
                            break

            if not (1 <= page <= 10):
                raise Exception

            await get_similar_maps(ch, map_id, page, filters)
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

    # find similar maps (sliders)
    if any(msg.startswith(C + s + ' ') for s in ['sl', 'slider']):
        msg = msg[msg.index(' ') + 1:]

        # parse input
        try:
            map_id = msg[:msg.index(' ')] if ' ' in msg else msg
            if '/' in map_id:
                map_id = map_id[map_id.strip('/').rindex('/') + 1:]
            map_id = ''.join(c for c in map_id if '0' <= c <= '9')

            page = 1
            if ' ' in msg:
                page = int(msg[msg.index(' ') + 1:])

            if not (1 <= page <= 10):
                raise Exception

            await get_slider_maps(ch, map_id, page)
        except:
            await send_error_message(ch)

    # find pp maps
    if msg.startswith(C + 'pp '):
        msg = msg[msg.index(' ') + 1:]

        # parse input
        try:
            params = msg.strip().split(' ')

            pp_boundaries = params[0]
            min_pp, max_pp = pp_boundaries.split('-')
            min_pp, max_pp = float(min_pp), float(max_pp)

            mods_include = ''
            mods_exclude = ''
            page = 1

            if len(params) > 1:
                # just page number
                if '0' <= params[1][0] <= '9':
                    page = int(params[1])
                # contains mod combos
                else:
                    # exclude
                    if params[1][0] == '-':
                        mods_exclude = params[1][1:]
                    else:
                        mods_include = params[1]
                    if len(params) > 2:
                        page = int(params[2])

            if not (1 <= page <= 10):
                raise Exception

            await get_pp_maps(ch, min_pp, max_pp, mods_include, mods_exclude, page)
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

    # farmer rating
    if any(msg.startswith(C + s) for s in ['f', 'farm', 'farmer']):
        if any(msg == C + s for s in ['f', 'farm', 'farmer']):
            username = au.display_name
        elif any(msg.startswith(C + s + ' ') for s in ['f', 'farm', 'farmer']):
            username = msg[msg.index(' ') + 1:]
        else:
            return

        await get_farmer_rating(ch, username)

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

client.run(tokens.beta_token if DEBUG else tokens.token)
