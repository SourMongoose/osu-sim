# https://discord.com/api/oauth2/authorize?client_id=829860591405498419&permissions=18432&scope=bot

import asyncio
import discord
import json
import math
import random
import time
import traceback

import api
#import estimaterank
import findppmaps
import similarity_buckets
import similarity_sliders
import similarity_srs
import tokens

# debugging
DEBUG = False

bot = discord.Bot()

async def send_error_message(ctx, msg='Invalid input.'):
    color = discord.Color.from_rgb(255, 100, 100)
    embed = discord.Embed(description=msg, color=color)
    await ctx.respond(embed=embed)

def get_error_message(msg='Invalid input.'):
    color = discord.Color.from_rgb(255, 100, 100)
    return discord.Embed(description=msg, color=color)

def id_to_map(id):
    mapstr = f'{stats[str(id)]["artist"]} - {stats[str(id)]["title"]} [{stats[str(id)]["version"]}]'
    return mapstr

def file_to_link(file):
    id = alphanumeric(file)
    return f'https://osu.ppy.sh/b/{id}' if id else ''

def username_to_id(username):
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
        return None

    return user['id']

async def send_output_pages(ctx, title, elements, page, edit_msg=False):
    perpage = 10
    if (page - 1) * perpage >= len(elements):
        page = 1

    color = discord.Color.from_rgb(100, 255, 100)

    def make_embed():
        description = '\n'.join(f'**{i+1})** {elements[i]}' for i in range((page - 1) * perpage, min(page * perpage, len(elements))))
        embed = discord.Embed(title=title, color=color, description=description)
        embed.set_footer(text=f'Page {page} of {(len(elements) - 1) // perpage + 1}')
        return embed

    class PagesView(discord.ui.View):
        async def on_timeout(self):
            await ctx.edit(view=None)

        @discord.ui.button(label='\u25C0', style=discord.ButtonStyle.primary, disabled=(page == 1))
        async def left_button_callback(self, button, interaction):
            nonlocal page
            page = max(1, page - 1)
            for child in self.children: # all children are no longer disabled, lets go
                child.disabled = False
            button.disabled = (page == 1)
            await interaction.response.edit_message(embed=make_embed(), view=self)

        @discord.ui.button(label='\u25B6', style=discord.ButtonStyle.primary, disabled=(page == (len(elements) - 1) // perpage + 1))
        async def right_button_callback(self, button, interaction):
            nonlocal page
            page = min((len(elements) - 1) // perpage + 1, page + 1)
            for child in self.children:
                child.disabled = False
            button.disabled = (page == (len(elements) - 1) // perpage + 1)
            await interaction.response.edit_message(embed=make_embed(), view=self)

    if edit_msg:
        await ctx.edit(embed=make_embed(), view=PagesView(timeout=30, disable_on_timeout=True))
    else:
        await ctx.respond(embed=make_embed(), view=PagesView(timeout=30, disable_on_timeout=True))

async def get_similar_maps(ctx, map_id, page=1, filters=None):
    perpage = 10
    n = 10 * perpage

    color = discord.Color.from_rgb(255, 255, 100)
    description = 'Calculating...'
    footer = 'This should take about 10 seconds.'
    embed = discord.Embed(description=description, color=color)
    embed.set_footer(text=footer)
    calc_msg = await ctx.respond(embed=embed)

    try:
        sim = similarity_buckets.get_similar(map_id, n, filters)
    except:
        await calc_msg.edit_original_response(embed=get_error_message())
        return

    if len(sim) == 0:
        await calc_msg.edit_original_response(embed=get_error_message('Not enough similar maps.'))
        return

    title = f'Maps similar in structure to {map_id}:'
    elements = [f'[{id_to_map(sim[i][0])}]({file_to_link(sim[i][0])})' for i in range(len(sim))]
    await send_output_pages(ctx, title, elements, page, edit_msg=True)

async def get_rating_maps(ctx, map_id, page=1, dt=False):
    perpage = 10
    n = 10 * perpage

    try:
        sim = similarity_srs.get_similar(map_id, n, ['DT'] if dt else [])
    except:
        await send_error_message(ctx)
        return

    if not sim:
        await send_error_message(ctx, 'Map not found in local database.')
        return

    title = f'Maps similar in star rating to {map_id}' + (' (+DT)' if dt else '') + ':'
    elements = [f'[{id_to_map(sim[i][0])}]({file_to_link(sim[i][0])})' for i in range(len(sim))]
    await send_output_pages(ctx, title, elements, page)

async def get_slider_maps(ctx, map_id, page=1):
    perpage = 10
    n = 10 * perpage

    color = discord.Color.from_rgb(255, 255, 100)
    description = 'Calculating...'
    footer = 'This should take about 10 seconds.'
    embed = discord.Embed(description=description, color=color)
    embed.set_footer(text=footer)
    calc_msg = await ctx.respond(embed=embed)

    try:
        sim = similarity_sliders.get_similar(map_id, n)
    except:
        await calc_msg.edit_original_response(get_error_message())
        return

    if len(sim) == 0:
        await calc_msg.edit_original_response(get_error_message('Not enough similar maps.'))
        return

    title = f'Maps similar in sliders to {map_id}:'
    elements = [f'[{id_to_map(sim[i][0].replace(".sldr",""))}]({file_to_link(sim[i][0])})' for i in range(len(sim))]
    await send_output_pages(ctx, title, elements, page)

async def get_pp_maps(ctx, min_pp=0., max_pp=2e9, mods_include='', mods_exclude='', page=1, filters=None):
    perpage = 10
    n = 10 * perpage

    try:
        mods_include, mods_exclude = findppmaps.simplify_mods(mods_include), findppmaps.simplify_mods(mods_exclude)
        maps = findppmaps.find_pp_maps(min_pp, max_pp, mods_include, mods_exclude, limit=n, filters=filters)
    except:
        await send_error_message(ctx)
        return

    if len(maps) == 0:
        await send_error_message(ctx, 'Not enough maps.')
        return

    title = f'Overweight maps from {min_pp}-{max_pp}pp'
    if mods_include:
        title += f', using mods {mods_include}'
    if mods_exclude:
        title += f', excluding mods {mods_exclude}'
    title += ':'
    modcombo = lambda i: f' +{maps[i][1]}' if maps[i][1] else ''
    elements = [f'[{id_to_map(maps[i][0])}](https://osu.ppy.sh/b/{maps[i][0]}){modcombo(i)}' for i in range(len(maps))]
    await send_output_pages(ctx, title, elements, page)

async def recommend_map(ctx, username):
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
        await send_error_message(ctx, f'User **{username}** not found.')
        return

    scores = None
    while counter < 3:
        try:
            scores = api.get_scores(user['id'], limit=50)
            break
        except:
            counter += 1

    if not scores:
        await send_error_message(ctx, f'Error fetching scores for user **{username}**. Please try again later.')
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
        await send_error_message(ctx, f'Error finding map recommendations for user **{username}**. Please try again later.')
        return

    score_ids = set(score['beatmap']['id'] for score in scores)

    farm_maps = []
    for i in range(len(sim)):
        map_id = alphanumeric(sim[i][0])
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
    description = f'**{id_to_map(sim[index][0])}**{modstr}\n{file_to_link(sim[index][0])}'
    embed = discord.Embed(description=description, color=color)
    embed.set_footer(text=f'Recommended map for {user["username"]}')
    await ctx.respond(embed=embed)

async def get_farmer_rating(ctx, username):
    id = username_to_id(username)

    if not id:
        await send_error_message(ctx, f'Error fetching scores for user **{username}**. Please try again later.')
        return

    scores = None
    counter = 0
    while counter < 3:
        try:
            scores = api.get_scores(id, limit=50) + api.get_scores(id, limit=50, offset=50)
            break
        except:
            counter += 1

    if not scores:
        await send_error_message(ctx, f'Error fetching scores for user **{username}**. Please try again later.')
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
    await ctx.respond(embed=embed)

'''
async def get_estimated_rank(ctx, username):
    id = username_to_id(username)

    if not id:
        await send_error_message(ctx, f'Error fetching scores for user **{username}**. Please try again later.')
        return

    try:
        er = estimaterank.get_rank_estimate(id)
    except ZeroDivisionError:
        await send_error_message(ctx, f'Error fetching scores for user **{username}**. Please try again later.')
        return

    color = discord.Color.from_rgb(100, 255, 100)
    title = f'Estimated rank for {username}:'
    description = f'**#{round(er[0])}**\n\n' + '\n'.join(f'**{round(sc[1])}** | {sc[0]}' for sc in er[1])
    embed = discord.Embed(title=title, description=description, color=color)
    await ctx.respond(embed=embed)
'''

async def chez(message):
    embeds = message.embeds
    if not embeds:
        return

    embed = embeds[0].to_dict()

    if 'author' not in embed:
        return

    if 'chezbananas on' in embed['author']['name']:
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
    elif 'Azurium on MATZcore [Lolicore]' in embed['author']['name']:
        await message.channel.send('shat on')
    elif 'Recent' in message.content:
        if embed['author']['name'].startswith('Lionheart'):
            await message.channel.send(
                'Like a lion :lion_face: we fight :punch: '
                'Together we will die :skull: '
                'For the glory of our god :innocent: '
                'Justice on our side :cross: '
                'This cross will lead to light :bulb: '
                'Follow Richard Lionheart :pray:')
        elif embed['author']['name'].startswith('Glory Days'):
            await message.channel.send(
                'To seek the glory days :sunrise: '
                'we\'ll fight the lion\'s way :lion_face: '
                'then let the rain wash :cloud_rain: '
                'all of your pride away :innocent: '
                'so if this victory :trophy: '
                'is our last odyssey :red_car: '
                'then let the POWER within us decide :muscle:')
        elif embed['author']['name'].startswith('Day By Day ft. Nicole Curry') \
                or embed['author']['name'].startswith('Day by day (PSYQUI Remix)'):
            await message.channel.send(
                'It\'s time to start the new day :sunrise: '
                'Put aside all the trouble on the way :put_litter_in_its_place: '
                'Get out of bed :bed: and brush my hair :woman_red_haired: and wear my favorite outfit :dress: '
                'I don\'t know what to do with myself :woman_shrugging: '
                'I just go on day by day :calendar_spiral: '
                'Being my very best me :blush:')

active_quizzes = {}
async def start_quiz(ctx, difficulty, first, guess_time, length, top_plays):
    ch = ctx.channel

    if ch.id in active_quizzes:
        return

    active_quizzes[ch.id] = {}
    q = active_quizzes[ch.id]

    q['first'] = first
    q['diff'] = False # diff

    pool = []
    difficulties = []
    if q['diff']:
        pass # easy, medium, hard, impossible, iceberg = easy_diffs, medium_diffs, hard_diffs, impossible_diffs, iceberg_diffs
    else:
        easy, medium, hard, impossible, iceberg = easy_sets, medium_sets, hard_sets, impossible_sets, iceberg_sets

    if top_plays and not q['diff']:
        usernames = top_plays.split(',')
        for i in range(len(usernames)):
            usernames[i] = usernames[i].strip()

        api.refresh_token()

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
        if 'easy' in difficulty:
            pool.extend(easy)
            difficulties.append('Easy')
        if 'medium' in difficulty:
            pool.extend(medium)
            difficulties.append('Medium')
        if 'hard' in difficulty:
            pool.extend(hard)
            difficulties.append('Hard')
        if 'impossible' in difficulty:
            pool.extend(impossible)
            difficulties.append('Impossible')
        if 'iceberg' in difficulty:
            pool.extend(iceberg)
            difficulties.append('Iceberg')

    if not pool:
        pool = easy
        difficulties = ['Easy']

    mapset_ids = []
    while len(mapset_ids) < length:
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

    if q['diff']:
        await ctx.respond(
            'Welcome to the osu! beatmap quiz! You will be given a series of difficulty names; try to type '
            'the title of the beatmap as quickly as possible.\n\n'
            f"Current settings: {'+'.join(difficulties)}, {length} songs, {guess_time}s guess time, {'first-guess' if q['first'] else 'time-based'} scoring\n\n"
            'First difficulty name will appear in 5 seconds!')
    else:
        await ctx.respond(
            'Welcome to the osu! beatmap quiz! You will be given a series of beatmap backgrounds; try to type '
            'the title of the beatmap as quickly as possible.\n\n'
            f"Current settings: {'+'.join(difficulties)}, {length} songs, {guess_time}s guess time, {'first-guess' if q['first'] else 'time-based'} scoring\n\n"
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

map_freq_country = get_map_freq('mapfreq_country.txt')

with open('stats.json', 'r') as f:
    stats = json.load(f)

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

# command starter
C = ',' if DEBUG else '.'

# supported symbols/keywords for search filters
symbols = ['!=', '>=', '<=', '>', '<', '=']
supported_filters = ['ar', 'od', 'hp', 'cs', 'length', 'sr', 'star', 'stars', 'aim', 'aimsr', 'tap', 'tapsr', 'id', 'max_bpm']

@bot.command(description='View commands')
async def help(ctx):
    title = 'Command List'
    color = discord.Color.from_rgb(150, 150, 150)
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
    await ctx.respond(embed=embed)

@bot.command(description='Get invite link')
async def invite(ctx):
    title = 'Invite this bot to your server:'
    color = discord.Color.from_rgb(150, 150, 150)
    description = 'https://discord.com/api/oauth2/authorize?client_id=829860591405498419&permissions=18432&scope=bot'
    embed = discord.Embed(title=title, description=description, color=color)
    await ctx.respond(embed=embed)

@bot.command(description='Find similar maps (based on map structure)')
async def sim(ctx,
              beatmap: discord.Option(str, description='beatmap id/link', required=True),
              filters: discord.Option(str, description='search filters', required=False),
              page: discord.Option(int, description='page', min_value=1, max_value=10, default=1, required=False)):
    # parse input
    try:
        if '/' in beatmap:
            beatmap = beatmap[beatmap.strip('/').rindex('/') + 1:]
        beatmap = ''.join(c for c in beatmap if '0' <= c <= '9')

        filters_list = []

        if filters:
            filters_split = filters.split(' ')
            for filter_str in filters_split:
                for symbol in symbols:
                    if symbol in filter_str:
                        filter_key = filter_str[:filter_str.index(symbol)]
                        filter_value = filter_str[filter_str.index(symbol) + len(symbol):]
                        if filter_key in supported_filters:
                            filters_list.append((filter_key, symbol, float(filter_value)))
                        else:
                            if filter_key:
                                await send_error_message(ctx, f'Filter `{filter_key}` not currently supported.')
                            else:
                                await send_error_message(ctx, "Don't include spaces when using filters (e.g. `ar<9` instead of `ar < 9`)")
                            return
                        break
    except:
        await send_error_message(ctx, traceback.format_exc())
        return

    await get_similar_maps(ctx, beatmap, page, filters_list)

@bot.command(description='Find similar maps (based on star rating)')
async def sr(ctx,
             beatmap: discord.Option(str, description='beatmap id/link', required=True),
             dt: discord.Option(bool, description='use DT star rating', default=False, required=False),
             page: discord.Option(int, description='page', min_value=1, max_value=10, default=1, required=False)):
    # parse input
    try:
        if '/' in beatmap:
            beatmap = beatmap[beatmap.strip('/').rindex('/') + 1:]
        beatmap = ''.join(c for c in beatmap if '0' <= c <= '9')

        await get_rating_maps(ctx, beatmap, page, dt)
    except:
        await send_error_message(ctx)

@bot.command(description='Find similar maps (based on slider velocity/length)')
async def slider(ctx,
                 beatmap: discord.Option(str, description='beatmap id/link', required=True),
                 page: discord.Option(int, description='page', min_value=1, max_value=10, default=1, required=False)):
    # parse input
    try:
        if '/' in beatmap:
            beatmap = beatmap[beatmap.strip('/').rindex('/') + 1:]
        beatmap = ''.join(c for c in beatmap if '0' <= c <= '9')

        await get_slider_maps(ctx, beatmap, page)
    except:
        await send_error_message(ctx)

@bot.command(description='Find overweighted maps')
async def pp(ctx,
             min_pp: discord.Option(float, description='minimum pp value', min_value=0, max_value=9999, default=0, required=False),
             max_pp: discord.Option(float, description='maximum pp value', min_value=0, max_value=9999, default=9999, required=False),
             mods_include: discord.Option(str, description='list of mods to include (will look for exact match)', default='', required=False),
             mods_exclude: discord.Option(str, description='list of mods to exclude', default='', required=False),
             filters: discord.Option(str, description='search filters', required=False),
             page: discord.Option(int, description='page', min_value=1, max_value=10, default=1, required=False)):
    # parse input
    try:
        filters_list = []

        if filters:
            filters_split = filters.split(' ')
            for filter_str in filters_split:
                for symbol in symbols:
                    if symbol in filter_str:
                        filter_key = filter_str[:filter_str.index(symbol)]
                        filter_value = filter_str[filter_str.index(symbol) + len(symbol):]
                        if filter_key in supported_filters:
                            filters_list.append((filter_key, symbol, float(filter_value)))
                        else:
                            if filter_key:
                                await send_error_message(ctx, f'Filter `{filter_key}` not currently supported.')
                            else:
                                await send_error_message(ctx, "Don't include spaces when using filters (e.g. `ar<9` instead of `ar < 9`)")
                            return
                        break

        await get_pp_maps(ctx, min_pp, max_pp, mods_include, mods_exclude, page, filters_list)
    except:
        await send_error_message(ctx, traceback.format_exc())

@bot.command(description='Recommend a map')
async def rec(ctx,
              username: discord.Option(str, description='osu! username', required=False)):
    if not username:
        username = ctx.author.display_name
    await recommend_map(ctx, username)

@bot.command(description='Get a user\'s farmer rating')
async def farmer(ctx,
                 username: discord.Option(str, description='osu! username', required=False)):
    if not username:
        username = ctx.author.display_name
    await get_farmer_rating(ctx, username)

'''
@bot.command(description='Get a user\'s estimated rank')
async def rank(ctx,
               username: discord.Option(str, description='osu! username', required=False)):
    if not username:
        username = ctx.author.display_name
    await get_estimated_rank(ctx, username)
'''

@bot.command(description='Start the osu! beatmap quiz')
async def quiz_start(ctx,
                difficulty: discord.Option(str, description='quiz difficulty(s)', default='easy', required=False),
                first: discord.Option(bool, description='first-guess scoring', default=False, required=False),
                guess_time: discord.Option(int, description='time for each guess (in seconds)', default=10, required=False),
                length: discord.Option(int, description='number of questions', default=10, required=False),
                top_plays: discord.Option(str, description='provide a list of comma-separated usernames to only use maps from those users\' top plays', required=False)):
    await start_quiz(ctx, difficulty, first, guess_time, length, top_plays)

@bot.command(description='Abort a currently running quiz')
async def quiz_abort(ctx):
    active_quizzes.pop(ctx.channel.id)
    await ctx.respond('Quiz has been aborted.')

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name='/help'))
    print('When you see it!')

@bot.event
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

    # beatmap bg trivia
    if ch.id in active_quizzes:
        await quiz_guess(au, ch, msg)

bot.run(tokens.beta_token if DEBUG else tokens.token)
