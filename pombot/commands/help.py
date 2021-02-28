from discord.ext.commands import Context


async def do_help(ctx: Context, *args):
    await ctx.send("do_help got: {}".format(" ".join(str(s) for s in args)))
