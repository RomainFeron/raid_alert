import discord
import logging
import os
import time
from discord.ext import commands, tasks
from dotenv import load_dotenv
from raid_alert import BossChecker, load_json_to_dict, get_boss_info

# General config
URL = 'https://l2unity.net/data/x10/boss'
BOSS_INFO_FILE_PATH = 'config/boss_info.json'
REFRESH_TIME = 30
HIGHLIGHT_RANGE = [0, 99]
FILTER_RANGE = [0, 99]
ALERT_STATUS = 'ON'

# Discord info stored in a .env file
load_dotenv()
BOT_TOKEN = os.getenv('DISCORD_TOKEN')
SERVER = os.getenv('DISCORD_SERVER')

# Logger format
logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s]::%(levelname)s  %(message)s',
                    datefmt='%Y.%m.%d - %H:%M:%S')

# Initialize BossChecker instance (scraper / parser for boss status)
boss_checker = BossChecker(url=URL)

# Initialize discord command bot instance (commands will start with !)
bot = commands.Bot('!')
bot.refresh_time = REFRESH_TIME
bot.highlight_range = HIGHLIGHT_RANGE
bot.filter_range = FILTER_RANGE
bot.alert_status = ALERT_STATUS

# Generate json file with boss info if it does not exist already
if not os.path.isfile(BOSS_INFO_FILE_PATH):
    get_boss_info(BOSS_INFO_FILE_PATH)

# Load boss info from JSON file
BOSS_INFO = load_json_to_dict(BOSS_INFO_FILE_PATH)


def format_boss_message(boss):
    '''
    '''
    drops = "/".join(BOSS_INFO[boss.name]["drops"]) if len(BOSS_INFO[boss.name]["drops"]) > 0 else 'No drops'
    spawn_time = boss.spawn_time.strftime("%H:%M") if boss.spawn_time is not None else 'unknown time'
    time_dead = boss.time_dead if boss.time_dead else 'unknown'
    adds = f'{BOSS_INFO[boss.name]["adds"][0]}-{BOSS_INFO[boss.name]["adds"][1]}' if BOSS_INFO[boss.name]["adds"] != [0, 0] else 'no'
    msg_string = (f'**[lvl {boss.level}]** {boss.name} spawned at {spawn_time}'
                  f' **[{drops}]**'
                  f' **[{adds} adds]**'
                  f' **[[map]({BOSS_INFO[boss.name]["map_url"]})]**'
                  f'  (time dead: {time_dead})')
    return msg_string


@tasks.loop(seconds=REFRESH_TIME)
async def boss_check():
    '''
    Routine task checking for updated boss status (death / spawn)
    '''
    # Retrieve server and channels IDs
    server = discord.utils.get(bot.guilds, name=SERVER)
    boss_kill_channel = discord.utils.get(server.channels, name='boss-kill')
    boss_spawn_channel = discord.utils.get(server.channels, name='boss-spawn')
    # Define filter and highlight ranges
    # Update boss status
    boss_checker.update()
    if len(boss_checker.updates) == 0:
        logging.info('Boss status checked: no update')
        return
    logging.info(f'Boss status checked: {boss_checker.updates}')
    # Generate a message for each boss with a status change
    for boss in boss_checker.updates:
        # Embedded instead of standard message to include a clickable link to the map
        if int(boss.level) not in range(bot.filter_range[0], bot.filter_range[-1] + 1):
            continue
        if int(boss.level) in range(bot.highlight_range[0], bot.highlight_range[-1] + 1):
            msg = discord.Embed(color=0x2ECC71)
        else:
            msg = discord.Embed()
        msg.description = ''
        if boss.has_died:
            lifespan = boss.lifespan if boss.lifespan else 'unknown time'
            msg = f'{boss.name} (lvl {boss.level}) was killed at {boss.time_of_death.strftime("%H:%M")} (lifespan: {lifespan})'
            await boss_kill_channel.send(msg)
        elif boss.has_spawned:
            msg.description = format_boss_message(boss)
            await boss_spawn_channel.send(embed=msg)


@bot.command()
async def commands(ctx):
    '''
    !commands command lists all available commands
    '''
    msg = 'Available commands:\n'
    msg += '**!alive**: list all bosses alive at the moment\n'
    msg += '**!start**: start the automated boss status updated\n'
    msg += '**!stop**: stop the automated boss status updated\n'
    msg += f'**!updatetime <n>** : change automated boss status check time to *n* seconds (current: {bot.refresh_time})\n'
    msg += f'**!setrange <min> <max>** : toggle alerts only for bosses between levels *min* and *max* (current: {bot.filter_range[0]}-{bot.filter_range[-1]})\n'
    msg += f'**!highlight <min> <max>** : highlight messages for bosses between levels *min* and *max* (current: {bot.highlight_range[0]}-{bot.highlight_range[-1]})\n'
    msg += f'**!config** : display current configuration\n'
    await ctx.channel.send(msg)


@bot.command()
async def alive(ctx):
    '''
    !alive command returns the list of boss that are alive at the moment
    '''
    alive_bosses = [boss for boss in boss_checker.bosses.values() if boss.status == 'alive']
    msg = discord.Embed()
    msg.description = ''
    for boss in alive_bosses:
        msg.description += '  - ' + format_boss_message(boss) + '\n'
    msg.set_thumbnail(url=discord.Embed.Empty)
    await ctx.channel.send(embed=msg)


@bot.command()
async def updatetime(ctx, time):
    '''
    !updatetime command changes boss status update time (default is 30s)
    '''
    try:
        bot.refresh_time = int(time)
        boss_check.change_interval(seconds=bot.refresh_time)
        await ctx.channel.send(f'Update time set to **{bot.refresh_time}** seconds')
    except ValueError:
        await ctx.channel.send(f'Invalid value **{time}** for update time; expected value is number of seconds.')
        return


@bot.command()
async def stop(ctx):
    '''
    !stop command stops automated boss status update
    '''
    if bot.alert_status == 'ON':
        await ctx.channel.send('Alerts stopped')
        bot.alert_status = 'OFF'
        boss_check.cancel()
    else:
        await ctx.channel.send('Alerts were already stopped')


@bot.command()
async def start(ctx):
    '''
    !start command starts automated boss status update
    '''
    wait_count = 0
    while boss_check.is_running() and wait_count < 10:
        time.sleep(1)
        wait_count += 1
    if bot.alert_status == 'OFF':
        await ctx.channel.send('Alerts started')
        bot.alert_status = 'ON'
        boss_check.start()
    else:
        await ctx.channel.send('Alerts were already started')


@bot.command()
async def highlight(ctx, min_level, max_level):
    '''
    !highlight command highlights messages for bosses within a specified level range
    '''
    try:
        bot.highlight_range = [int(min_level), int(max_level)]
        await ctx.channel.send(f'Highlight level range set to **{min_level}-{max_level}**')
    except ValueError:
        await ctx.channel.send(f'Invalid value **{min_level} {max_level}** for highlight range (expected: *min-level max-level*)')


@bot.command()
async def setrange(ctx, min_level, max_level):
    '''
    !setrange command filters out messages for bosses outside of the specified level range
    '''
    try:
        bot.filter_range = [int(min_level), int(max_level)]
        await ctx.channel.send(f'Filter level range set to **{min_level}-{max_level}**')
    except ValueError:
        await ctx.channel.send(f'Invalid value **{min_level} {max_level}** for filter range (expected: *min-level max-level*)')


@bot.command()
async def config(ctx):
    '''
    !stop command stops automated boss status update
    '''
    msg = f' - Alerts: **{bot.alert_status}**\n'
    msg += f' - Lvl filter range: **{bot.filter_range[0]} - {bot.filter_range[-1]}**\n'
    msg += f' - Lvl highlight range: **{bot.highlight_range[0]} - {bot.highlight_range[-1]}**\n'
    msg += f' - Update interval: **{bot.refresh_time}** seconds\n'
    await ctx.channel.send(msg)


@bot.event
async def on_connect():
    logging.info('Connecting to discord')


@bot.event
async def on_ready():
    logging.info('Connection successful')
    server = discord.utils.get(bot.guilds, name=SERVER)
    boss_kill_channel = discord.utils.get(server.channels, name='boss-kill')
    boss_spawn_channel = discord.utils.get(server.channels, name='boss-spawn')
    msg = 'Raid alerts **ON**'
    await boss_kill_channel.send(msg)
    await boss_spawn_channel.send(msg)
    boss_check.start()


@bot.event
async def on_resumed():
    logging.info('Connection resumed')


bot.run(BOT_TOKEN)
