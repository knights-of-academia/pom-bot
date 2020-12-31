# Pomodoro Event Spec Sheet - Expanded

[Discord](#) - request access
[ERD](https://dbdiagram.io/d/5fa190533a78976d7b7a5c0a)

- Two teams, knights and vikings.
- All KOA participants are automatically Knights. Depending on balancing, one other partner may also be on the team "Knights".
    - In the event that our partners are "slacking", we may want to change this over to completely random matchmaking for both KOA and partners.
    - The first week will be a practice run. We will record scores on both teams, and ensure both teams are balanced and all major holes are patched before the actual event begins.

## Hitpoints System

### 11/28/2020

**Colin** - I think we should stick with the original system for right now. Each team starts with 0 "hitpoints" and as they move forward the team that takes the least damage wins. Something to consult Mikymac on. 

## Spec Sheet

- [ ] Pom Cap of 10
    - One day is 24 hours from the first pom they log. (maybe? that's how it was last time)
- [ ] User chooses between three actions depending on your risk tolerance level.
        - Attacking
            - [ ] Low risk, low reward
            - [ ] Medium risk, medium reward
            - [ ] High risk, high reward
                - Critical strikes / You have a low chance to strike critical damage with any action command. This is a pleasant surprise when it happens, but does not frustrate the user as we've seen with the riskier command (bomb) in our last event.
        - Defense
            - [ ] Repair?
            - [ ] Defend future attacks
    - Only poms logged with an action are immediately counted towards the war (see cost system).
    - After 10 poms in a day, all action poms are failing.
- [ ] Cost system
    - Users must have a certain amount of Poms "banked" to perform an action
        - Attacking should have a higher cost depending on the reward level (low, medium, high).
        - Defense should be lower than attack.
    - *This concept still needs to be balanced.*
        - Best case scenario: admins can edit costs quickly to balance.
            - Any balance changes would be sent in war channels and pinned by the bot.
    - Players can team up to perform an action.

> Users should not be able to exploit these three actions. Users must also feel motivated to take on a particular strategy. It's up to us to add the magic, making it fun to participate and ensuring that it doesn't break down in any one place. 

- [ ] Setting up our partners for event
    - Alex is working on acquiring partners for the event.
    - Making the bot work on separate servers
        - [ ] Remove channel specific barrier, store channels in database instead
            - Make a channel a pom channel by an admin running `!setchannel Pom` or something
        - [ ] Storing users (userId, guildId of guild they joined from, teamId)
        - [ ] Should users see poms from any participating server they're in?

> The goal is for this bot to be hosted on our partners servers directly. The bot must be able to take input via commands from all partnered servers, reporting to one universal database. Bonus cookies for making that database embedded into the bot itself! :cookie:

## Co-op Pomming

There's two routes to take with this idea.

- Battle Horace Integration
    - Users start poms through Battle Horace, a discord bot built as it's own pom timer.
    - Once a pom is completed, all users participating have a pom banked.
- Opt-in participation
    - users in raid-room or other channels can request another user to join them in a pom
    - after 25 minutes, each user must confirm they are still participating.

This would be a stretch goal for the event (feature to add if we complete everything else).

## Misc. Feature Suggestions

- First poms of the day - Increased probability of completing risky actions successfully for first 3-5 poms out of 10. Motivates ALL users to jump in, including the lower pommers. Yay for teamwork!
- ~~Building walls - The event alternates between two phases, build and attack. During build, your team works to build your defenses. During attack, you focus on destroying those defences first in order to attack the enemy directly.~~ Concept eliminated to simplify the event.
- Cooperation Bonuses - Users gain increased probability/damage when pomming with team members. This is only currently possible via Battle Horace. (see cost system as well)
- [ ] Taunts - Kevin had dreamed up the ability to taunt your opponent, likely for some sort of bonus or message sent to enemy team.
    - Ascii-art vs. embeds?
    - [ ] Cooldown needed (only one can be sent every 30 minutes)
    - Do we make it cost a pom?
    - Easy feature, simple to implement.