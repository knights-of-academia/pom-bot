# Pom Wars Attacks

An object model of attacks built from this directory structure and its
contents. Each subdirectory inside the `*_attacks/` folders contains an
"attack"; the name of that directory is the attack name (this is only
documented in the directory name, not in the `meta.json` therein).

It is intended that a developer can add a new attack by copy/pasting an
existing attack and modifying both its text and attributes via `meta.json`.

## Message.txt

This is a text file that is converted to markdown before posting. The text
itself will appear in a "pre-formatted" code block to separate it from the
other user chat in the same window.

Some manipulation is required to make it look good: Any single newline is
removed. For any consecutive series of newlines, all but the final two
newlines are removed. This is done so that the text in your code editor looks
normal (80-character limit) but also formats correctly across all screen
sizes in Discord.

## meta.json

All values in this file are non-negative, floating point numbers.

- *damage_multiplier*: A mostly non-zero number relative to 1.

    Normally, any attack will inflict its base damage defined in `config.py`
    and then reset the current total damage modification amount. This field
    will be multiplied by that base-amount. Except in the case of zero.

    In the specific case of zero, the attack will do no damage.

- *chance_for_this_attack*: A non-zero number.

  The chance that this attack, relative to other attacks of the same
  strength, will be chosen as this turn's attack. For example, given three
  attacks—Arrows, Swords and Hawks—if both Arrows and Swords have a chance of
  `1.0` for occuring and Hawks has only an `0.05` chance, then the occurence
  of each after 100 attacks might resemble:

  - Swords: 49 times
  - Arrows: 48 times
  - Hawks: 3 times

  Of course, given their random nature, these will occur at any time. There
  is no guarantee of even distribution.

## Criticals

For any strength of attack, there is a special directory named `~criticals`.

### Directory structure

The directory structure of `~criticals` follows any of the aforementioned
`*_attacks/` directories: Each sub-directory is the name of an attack and its
contents contain at least `message.txt` and `meta.json`. The difference is in
how these attacks are chosen.

### Code path

For any attack, there is a likelyhood of succeeding defined in `config.py`.
After considering this, another dice roll is taken to decide whether or not
this attack is a critical strike (also in `config.py`). If so, the same rules
for non-critical attacks apply to critical attacks given their probability.

Attacks in any given `~criticals/` directory may have their meta-attributes
buffed significantly.
