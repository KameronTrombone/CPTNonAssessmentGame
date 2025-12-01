import tcod 

from actions import EscapeAction, MovementAction
from input_handlers import EventHandler

health = 10
strength = 6
dexterity = 6
intelligence = 6

professions = ["fighter", "ranger", "wizard"]
races = ["human", "orc", "elf", "gnome"]

def main() -> None:
    screen_width = 80
    screen_height = 50

    player_x = int(screen_width / 2)
    player_y = int(screen_height / 2)



    tileset = tcod.tileset.load_tilesheet(
        "dejavu10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
    )

    event_handler = EventHandler()

    with tcod.context.new_terminal(
        screen_width,
        screen_height,
        tileset=tileset,
        title="Yet Another Roguelike Tutorial",
        vsync=True,
    ) as context:
        root_console = tcod.Console(screen_width, screen_height, order="F")
        while True:
            root_console.print(x=player_x, y=player_y, string="@")

            context.present(root_console)

            root_console.clear()

            for event in tcod.event.wait():
                action = event_handler.dispatch(event)
            if action is None:
                continue
            if isinstance(action, MovementAction):
                player_x += action.dx
                player_y += action.dy
            elif isinstance(action, EscapeAction):
                raise SystemExit()

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


