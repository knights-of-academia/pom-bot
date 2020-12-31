# Damage in the Pom Wars

Damage is generally a number relative to the base damages specified in the
.env:

BASE_DAMAGE_FOR_NORMAL_ATTACKS = '10'
BASE_DAMAGE_FOR_HEAVY_ATTACKS = '40'

Because buffs and defenses work with percentages of these numbers, doing
simple integer division and multiplication would result in some buffs being
far too powerful and some defends being non-existent.

Storing floating point number in databases is error prone. Even more so when
we care about exact values for an exact number of digits. As such, the way
damage is reported to the user is as it is specified in the configuration,
but the way damage is stored in the DB is different.

Upon inserting a new row to the actions table with some specified amount of
damage, the damage (float like "10.45") is multiplied by 1000 (ie. int like
"1045")

Upon retrieving that amount of damage from the database, an ORM function (or
other user function) should convert the stored integer number back to a
"real" damage by dividing it by 100.
