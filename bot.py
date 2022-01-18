import nextcord
from nextcord.ext import commands
from dotenv import dotenv_values
import sqlite3

con = sqlite3.connect('database.db')
cur = con.cursor()

intents = nextcord.Intents.default()
intents.typing = False
intents.presences = False
intents.members = True

bot = commands.Bot(command_prefix='*', intents=intents)
env = dotenv_values(".env")


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


@bot.listen('on_message')
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.lower().startswith('hallo bot'):
        await message.channel.send(f'Hallo {message.author.mention}!')


config = {}
bot.load_extension("cogs.settings", extras={
    "sqlitecon": con,
    "sqlitecur": cur,
    "config": config
})
bot.load_extension("cogs.roll", extras={
    "sqlitecon": con,
    "sqlitecur": cur,
    "config": config
})
bot.load_extension("cogs.invite", extras={
    "sqlitecon": con,
    "sqlitecur": cur,
    "config": config
})
bot.load_extension("cogs.foundry", extras={
    "sqlitecon": con,
    "sqlitecur": cur,
    "config": config,
    "foundryurl": env['FOUNDRY_URL']
})
bot.load_extension("cogs.groups", extras={
    "sqlitecon": con,
    "sqlitecur": cur,
    "config": config
})

bot.run(env['BOT_TOKEN'])
