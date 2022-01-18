import random
import re

from discord.ext import commands


class Roll(commands.Cog):
    def __init__(self, bot, con, cur, config):
        self.bot = bot
        self.con = con
        self.cur = cur
        self.config = config

    @commands.command(
        aliases=["r"],
        help="Wirft einen Würfel",
        usage="[anzahl der würfel]d[augenzahl]; Z.B.: 3d6 oder 1d2",
    )
    async def roll(self, ctx, dices):
        if re.match(r"\d+[dw]\d+", dices):
            dices = re.split(r"[dw]", dices)
            dice_count = int(dices[0])
            dice_type = int(dices[1])
            if dice_type >= 2:
                results = []
                for x in range(dice_count):
                    rand = random.randint((1 if dice_type > 2 else 0), (dice_type if dice_type > 2 else dice_type-1))
                    if dice_type == 2:
                        rand = "Kopf" if rand == 0 else "Zahl"
                    results.append(rand)
                string_results = [str(int) for int in results]
                await ctx.send(f'Würfelergebnis: ``{", ".join(string_results)}``')
            else:
                await ctx.send("Eine Augenzahl kleiner als 2 ist nicht zulässig.")
        else:
            await ctx.send("Die gewünschten Würfel wurden in einem falschen Format angegeben. "
                           "Bitte verwende [anzahl der Würfel]d[Augenzahl]. Zb 2d6 oder 1d2")


def setup(bot, **extras):
    con = extras["sqlitecon"]
    cur = extras["sqlitecur"]
    config = extras["config"]
    bot.add_cog(Roll(bot, con, cur, config))
