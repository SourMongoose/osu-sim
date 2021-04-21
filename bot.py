# https://discord.com/api/oauth2/authorize?client_id=829860591405498419&permissions=18432&scope=bot

import discord

import similarity_buckets
import similarity_srs
import tokens

client = discord.Client()

async def invalid_input(ch):
    color = discord.Color.from_rgb(255, 100, 100)
    description = 'Invalid input.'
    embed = discord.Embed(description=description, color=color)
    await ch.send(embed=embed)

async def get_similar_maps(ch, map_id, page=1):
    perpage = 10
    n = page * perpage

    color = discord.Color.from_rgb(255, 255, 100)
    description = 'Calculating...'
    footer = 'This should take about 5 seconds.'
    embed = discord.Embed(description=description, color=color)
    embed.set_footer(text=footer)
    calc_msg = await ch.send(embed=embed)

    try:
        sim = similarity_buckets.get_similar(map_id, n)
    except:
        await calc_msg.delete()
        await invalid_input(ch)
        return

    color = discord.Color.from_rgb(100, 255, 100)
    title = f'Maps similar to {map_id}:'
    file_to_link = lambda f: f'https://osu.ppy.sh/b/{map_ids[f.replace(".dist", "")]}' if f.replace(".dist", "") in map_ids else ''
    description = '\n'.join(f'**{i+1})** {sim[i][0].replace(".osu.dist","")}\n{file_to_link(sim[i][0])}' for i in range((page-1)*perpage, page*perpage))
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text=f'Page {page} of 10')
    await calc_msg.edit(embed=embed)

async def get_rating_maps(ch, map_id, page=1):
    perpage = 10
    n = page * perpage

    try:
        sim = similarity_srs.get_similar(map_id, n)
    except:
        await invalid_input(ch)
        return

    color = discord.Color.from_rgb(100, 255, 100)
    title = f'Maps similar to {map_id}:'
    file_to_link = lambda f: f'https://osu.ppy.sh/b/{map_ids[f+".osu"]}' if f+".osu" in map_ids else ''
    description = '\n'.join(f'**{i+1})** {sim[i][0].replace(".osu.dist","")}\n{file_to_link(sim[i][0])}' for i in range((page-1)*perpage, page*perpage))
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text=f'Page {page} of 10')
    await ch.send(embed=embed)

def get_map_ids():
    map_ids = {}

    with open('filenames.txt', 'r') as f:
        lines = f.readlines()

    for i in range(0, len(lines), 2):
        map_ids[lines[i + 1].strip()] = lines[i].strip()

    return map_ids

map_ids = get_map_ids()

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
        description = f'**{C}s**im `<beatmap id/link>` `[page]`\nFind similar maps (based on map structure)\n\n' \
                      f'**{C}r**ating `<beatmap id/link>` `[page]`\nFind similar maps (based on star rating)\n\n' \
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
    if any(msg.startswith(C+s+' ') for s in ['s', 'sim', 'similar']):
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
            await invalid_input(ch)

    # find similar maps (star rating)
    if any(msg.startswith(C + s + ' ') for s in ['r', 'rating']):
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

            await get_rating_maps(ch, map_id, page)
        except:
            await invalid_input(ch)

client.run(tokens.token)