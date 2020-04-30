#!/usr/bin/env python3
# bot.py

import os, sys
from dotenv import load_dotenv
from discord.ext import commands
from discord import embeds
import pymongo
from datetime import datetime
from collections import Counter
import re

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
print(TOKEN)
MONGO_IP = "mongodb://localhost:27017/"
POM_TRACK_LIMIT = 10
DESCRIPTION_LIMIT = 30
POM_CHANNEL_ID = 695007275995103332
MULTILINE_DESCRIPTION_DISABLED = True
bot = commands.Bot(command_prefix='!', case_insensitive=True)


'''
Create connection to database
'''
dbo = pymongo.MongoClient(MONGO_IP)
db = dbo["poms"]
pomcollection = db["tracked"]

"""
Tracks a new pom for the user.
"""


@bot.command(name='pom',
             help='Adds a new pom, if the first word in the description is a number (1-10), multiple poms will be '
                  'added with the given description.',
             pass_context=True)
async def pom(ctx, *, description: str = None):
    pom_count = 1

    try:
        if description:
            # If there is a description, check if the first word is a digit
            # And if it is, split the string to remove the digits length plus 1 for space.
            if description.split(' ', 1)[0].isdigit():
                pom_count = int(description.split(' ', 1)[0])
                if pom_count > POM_TRACK_LIMIT or pom_count < 1:
                    await ctx.message.add_reaction("⚠️")
                    await ctx.send('You can only add between 1 and 10 poms at once.')
                    return

                description = description[(len(str(pom_count)) + 1):]

        # Check if the description is too long
        if description is not None and len(description) > DESCRIPTION_LIMIT:
            await ctx.message.add_reaction("⚠️")
            await ctx.send('Your pom description must be less than 30 characters.')
            return

        if description is not None and "\n" in description and MULTILINE_DESCRIPTION_DISABLED:
            await ctx.message.add_reaction("⚠️")
            await ctx.send('Multi line pom descriptions are disabled.')
            return

        poms_to_add = []
        for _ in range(pom_count):
            if description:
                new_added_pom = {
                    "user_id": ctx.message.author.id,
                    "description": description,
                    "timestamp": datetime.now(),
                    "current_session": True
                }
            else:
                new_added_pom = {
                    "user_id": ctx.message.author.id,
                    "timestamp": datetime.now(),
                    "current_session": True
                }
            poms_to_add.append(new_added_pom)

        pomcollection.insert_many(poms_to_add, ordered=False)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        await ctx.message.add_reaction("🐛")
        f = open('errors.log', 'a')
        f.write(e)
        f.close()
        print(e)
    await ctx.message.add_reaction("🍅")


"""
Starts a new session for the user, meaning that all the poms in their current session will have their current_session
property set to false. 
"""


@bot.command(name='newleaf', help='Turn over a new leaf and hide the details of your previously tracked poms. Starts '
                                  'a new session.', pass_context=True)
async def new_session(ctx):
    document_count = pomcollection.count_documents({"user_id": ctx.message.author.id})

    # If the user tries to start a new session before doing anything
    if document_count == 0:
        await ctx.message.add_reaction("🍂")
        await ctx.send("A new session will be started when you track your first pom.")
        return

    # Set all previous poms to not be in the current session
    query = {"user_id": ctx.message.author.id, "current_session": True}
    update = {"$set": {"current_session": False}}
    pomcollection.update_many(query, update)
    await ctx.message.add_reaction("🍃")
    await ctx.send("A new session will be started when you track your next pom, {}."
                   .format(ctx.message.author.display_name))


"""
Gives the user an overview of how many poms they've been doing so far.
"""


@bot.command(name='poms', help='See details for your tracked poms and the current session.', pass_context=True)
async def poms(ctx):
    # Fetch all poms for user based on their Discord ID
    own_poms = list(pomcollection.find({"user_id": ctx.message.author.id}))

    # If the user has no tracked poms
    if len(own_poms) == 0 or own_poms is None:
        await ctx.message.add_reaction("⚠️")
        await ctx.send("You have no tracked poms.")
        return

    # All poms tracked this session by user
    session_poms = [x for x in own_poms if x["current_session"] is True]

    # Add a timestamp for session start, if a pom is tracked in this session
    if len(session_poms) > 0:
        try:
            time_now = datetime.now()
            time_then = session_poms[0]["timestamp"]
            duration_in_s = (time_now - time_then).total_seconds()
            days = int(duration_in_s // (24 * 3600))

            duration_in_s = duration_in_s % (24 * 3600)
            hours = int(duration_in_s // 3600)

            duration_in_s %= 3600
            minutes = int(duration_in_s // 60)

            session_start = "{} days, {} hours, {} minutes".format(days, hours, minutes)
        except Exception as e:
            await ctx.message.add_reaction("🐛")
            f = open('errors.log', 'a')
            f.write(e)
            f.close()
            print(e)
    else:
        session_start = "Not started yet"

    # Group poms by their description
    session_described_poms = []
    for p in session_poms:
        if 'description' in p:
            session_described_poms.append(p)
    described_poms_amount = len(session_described_poms)
    session_described_poms = Counter(des_pom["description"].capitalize() for des_pom in session_described_poms)
    # Set variable to see how many poms the user has.
    session_pom_amount = len(session_poms)
    total_pom_amount = len(own_poms)

    # Generate the embed for sending to the user
    title_embed = "Pom statistics for {}".format(ctx.message.author.display_name)
    description_embed = "**Pom statistics**\n" \
                        "Session started: *{}*\n" \
                        "Total poms this session: *{}*\n" \
                        "Accumulated poms: *{}*\n" \
                        "\n" \
                        "**Poms this session**\n" \
        .format(session_start, session_pom_amount, total_pom_amount)

    # Added description poms, sorted by how common they are
    for p in session_described_poms.most_common():
        description_embed += "{}: {}\n".format(p[0], p[1])

    # Add non-described count, if applicable
    undesignated_pom_count = session_pom_amount - described_poms_amount
    if undesignated_pom_count > 0:
        description_embed += "*Undesignated poms: {}*".format(undesignated_pom_count)

    # Generate embed message to send
    embedded_message = embeds.Embed(description=description_embed, colour=0xff6347) \
        .set_author(name=title_embed, icon_url="https://i.imgur.com/qRoH5B5.png")

    await ctx.send(embed=embedded_message)


"""
Gives the user an overview of how many poms they've been doing so far.
"""


@bot.command(name='howmany', help='List your poms with a given description.', pass_context=True)
async def howmany(ctx, *, description: str = None):
    if description is None:
        await ctx.message.add_reaction("⚠️")
        await ctx.send("You must specify a description to search for.")
        return

    # Fetch all poms for user based on their Discord ID
    own_poms = list(pomcollection.find({
        "user_id": ctx.message.author.id,
        "description": re.compile('^' + re.escape(description) + '$', re.IGNORECASE)
    }))

    # If the user has no tracked poms
    if len(own_poms) == 0 or own_poms is None:
        await ctx.message.add_reaction("⚠️")
        await ctx.send("You have no tracked poms with that description.")
        return
    total_pom_amount = len(own_poms)

    await ctx.message.add_reaction("🧮")
    await ctx.send("You have {} pom(s) with the description {}".format(total_pom_amount, description))


"""
Undoes / removes your x latest poms. Default is 1 latest.
"""


@bot.command(name='undo', help="Undo/remove your x latest poms. If no number is specified, only the newest pom will "
                               "be undone.")
async def remove(ctx, *, count: str = None):
    pom_count = 1
    if count:
        if count.split(' ', 1)[0].isdigit():
            pom_count = int(count.split(' ', 1)[0])
            if pom_count > POM_TRACK_LIMIT:
                await ctx.message.add_reaction("⚠️")
                await ctx.send('You can only undo up to 10 poms at once.')
                return

    try:
        to_delete = pomcollection.find({"user_id": ctx.message.author.id}).limit(pom_count).sort("timestamp", -1)

        to_delete_ids = []
        for pom_to_delete in to_delete:
            to_delete_ids.append(pom_to_delete['_id'])
        pomcollection.delete_many({"_id": {'$in': to_delete_ids}})

    except Exception as e:
        await ctx.message.add_reaction("🐛")
        f = open('errors.log', 'a')
        f.write(e)
        f.close()
        print(e)

    await ctx.message.add_reaction("↩")


"""
Remove your x latest poms. Default is 1 latest.
"""


@bot.command(name='reset', help="Permanently deletes all your poms. WARNING: There's no undoing this.")
async def remove(ctx):
    try:
        pomcollection.delete_many({"user_id": ctx.message.author.id})

    except Exception as e:
        await ctx.message.add_reaction("🐛")
        f = open('errors.log', 'a')
        f.write(e)
        f.close()
        print(e)

    await ctx.message.add_reaction("🗑️")


"""
ADMIN COMMAND:
Allows guardians and helpers to see the total amount of poms completed by KOA users since ever.
"""


@bot.command(name='total', help='List total amount of poms.')
@commands.has_any_role('Guardians', 'Helpers')
async def total(ctx):
    document_count = pomcollection.estimated_document_count()
    await ctx.send("Total amount of poms: {}".format(document_count))


'''
If user tries to use a command that they do not have access to
'''


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.message.add_reaction("⚠️")
        await ctx.send('You do not have the correct role for this command.')


'''
Limit to certain channels, must process commands afterwards,
or they'll stop working.
'''


@bot.event
async def on_message(message):
    if message.channel.id != POM_CHANNEL_ID:
        return
    await bot.process_commands(message)


bot.run(TOKEN)
