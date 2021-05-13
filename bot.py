# https://discord.com/api/oauth2/authorize?client_id=829860591405498419&permissions=18432&scope=bot

import discord
import random

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
        await send_error_message(ch, 'Error fetching scores. Please try again later.')
        return

    score_ids = set(score['beatmap']['id'] for score in scores)

    index = 0
    for i in range(len(sim)):
        map_id = file_to_id(sim[i][0])
        if int(map_id) in score_ids:
            continue
        if map_freq.get(map_id, 0) >= 100: # frequency threshold
            index = i
            if random.randrange(2):
                break

    color = discord.Color.from_rgb(100, 255, 100)
    modstr = ' +' + ''.join(scores[score_index]['mods']) if scores[score_index]['mods'] else ''
    description = f'**{sim[index][0]}**{modstr}\n{file_to_link(sim[index][0])}'
    embed = discord.Embed(description=description, color=color)
    embed.set_footer(text=f'Recommended map for {user["username"]}')
    await ch.send(embed=embed)

def get_map_ids():
    map_ids = {}

    with open('filenames.txt', 'r') as f:
        lines = f.readlines()

    for i in range(0, len(lines), 2):
        map_ids[lines[i + 1].strip().lower()] = lines[i].strip()

    return map_ids

def get_map_freq():
    map_freq = {}

    with open('mapfreq.txt', 'r') as f:
        lines = f.readlines()

    for line in lines:
        id, freq = line.split(',')
        map_freq[id] = int(freq)

    return map_freq

map_ids = get_map_ids()
map_freq = get_map_freq()

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

client.run(tokens.beta_token)