# https://discord.com/api/oauth2/authorize?client_id=829860591405498419&permissions=51200&scope=bot

import discord

import similarity_buckets
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
    footer = 'This should take about 30 seconds.'
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
    description = '\n'.join(f'**{i+1})** {sim[i][0].replace(".osu.dist","")}' for i in range((page-1)*perpage, page*perpage))
    embed = discord.Embed(title=title, description=description, color=color)
    await calc_msg.edit(embed=embed)

# command starter
C = '.'

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name=C+'help'))
    print('When you see it!')

@client.event
async def on_message(message):
    global trading_enabled

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
        description = f'**{C}s**im `<beatmap id/link>` `[page]`\nFind similar maps\n\n' \
                      f'**{C}h**elp\nView commands'
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text="Omit brackets. Square brackets ([]) indicate optional parameters.")
        await ch.send(embed=embed)

    # find similar maps
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

client.run(tokens.token)