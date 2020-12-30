# Pom Wars Setup

A Pom War is an event held among multiple Discord guilds where each guild can
choose to have members of only a specific team or multiple teams.

To get a guild ready for the event, decide which is right for your guild.

## Single-team guilds

- Add the bot to the guild
- Make a role called either "Knight" or "Viking"
- Make a channel called "#the-draft"
- Make a channel where ! actions will be put (#battlegrounds)
  - Set permissions so that only players with the chosen role can see this
    channel
- Give Debashis the guild ID
- Give Debashis the exact name of the channel created

## Any-team guilds

- Add the bot to the guild
- Make two roles called "Knight" and "Viking"
- Make a channel called "#the-draft"
- Make a channel where ! actions will be put for each Role (eg. #knights,
  #vikings)
  - Set permissions so that only players with the role for each channel can
    see that channel and not the other
- Give Debashis the exact name of both channels created

## Addition steps for configure before and after a beta

For beta

- Make #the-draft invisible to everybody except the beta testers

For "live":

- Remove the restrictions on the #the-draft channel


## Inviting the bot to partner servers
- Go to the [Discord Developer Portal](https://discord.com/developers/applications)
- Click on the application associated with the bot, or create a new application if necessary.
- Select 'Bot' in the sidebar.
  - Click 'Add Bot' if a bot is not already shown. This creates the bot account that will be invited to partner servers.
  - Make sure the 'Public Bot' switch is on, as this will allow partners to use the link to invite the bot to their servers.
- Select 'General Information' in the sidebar.
  - To generate the invite link, copy the client ID and paste it into the link below to replace [YOUR CLIENT ID]
  - https://discord.com/api/oauth2/authorize?permissions=268782656&scope=bot&client_id=[YOUR CLIENT ID]
    - The link uses permission integer 268782656, which allows the permissions:
      - Manage Roles
      - View Channels
      - Send Messages
      - Embed Links
      - Read Message History
      - Use External Emojis
      - Add Reactions
- Send the link to a few people on the team, so they can verify that the link works as intended.
- If the link works correctly, send the link to the partners who will be inviting the bot to their servers.
