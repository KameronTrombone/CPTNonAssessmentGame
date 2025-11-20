
health = 10
strength = 6
dexterity = 6
intelligence = 6
proffesions = [fighter, ranger, wizard]
races = [human, orc, elf, gnome]

def main():
    proffesion = proffesions[int(input("What class would you like to be ? Type '0' for fighter, '1' for ranger, or '2', for wizard" ))]
    if proffesion == fighter:
        "blah blah blah"
    elif proffesion == ranger:
        "blah blah blah"
    elif proffesion == wizard:
        "blah blah blah"
    else:
        proffesion = fighter
        print('you are stupid, be a fighter')
   
    race = races[int(input("What race would you like to be ? Type '0' for human, '1' for orc, '2' for elf, or '3' for gnome"))]
    if race == human:
        strength += 0
        dexterity -= 0
        intelligence -= 0
    elif race == orc:
        strength += 2
        dexterity -= 1
        intelligence -= 1
    elif race == elf:
        strength -= 2
        dexterity += 1
        intelligence += 1
    elif race == gnome:
        strength -=1
        dexterity += 0
        intelligence += 2
        health -= 1
    print(proffesion, race) 

