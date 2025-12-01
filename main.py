health = 10
strength = 6
dexterity = 6
intelligence = 6

professions = ["fighter", "ranger", "wizard"]
races = ["human", "orc", "elf", "gnome"]

def main():
    global health, strength, dexterity, intelligence
    
    profession = professions[int(input("Choose class: 0=fighter, 1=ranger, 2=wizard: "))]
    if profession == "fighter":
        print("You are a strong fighter, ready for battle!")
    elif profession == "ranger":
        print("You are a nimble ranger, master of the wilds!")
    elif profession == "wizard":
        print("You are a wise wizard, wielder of arcane power!")
    else:
        profession = "fighter"
        print("Invalid choice. Defaulting to fighter.")

    race = races[int(input("Choose race: 0=human, 1=orc, 2=elf, 3=gnome: "))]
    if race == "human":
        pass  # no stat changes
    elif race == "orc":
        strength += 2
        dexterity -= 1
        intelligence -= 1
    elif race == "elf":
        strength -= 2
        dexterity += 1
        intelligence += 1
    elif race == "gnome":
        strength -= 1
        intelligence += 2
        health -= 1
        
    print("\n--- Character Created ---")
    print(f"Profession: {profession}")
    print(f"Race: {race}")
    print(f"Stats -> Health: {health}, Strength: {strength}, Dexterity: {dexterity}, Intelligence: {intelligence}")

if __name__ == "__main__":
    main()

    