#!/usr/bin/env python3
# rogue_ascii_v2.py
# Upgraded ASCII roguelike — colours, larger
# UI, simple inventory, weapon equip, powerups.
# Save & run with: python3 rogue_ascii_v2.py
# On Windows: pip install windows-curses

import curses
import random
import sys

MAP_W = 100
MAP_H = 30
MAX_ROOMS = 14
ROOM_MIN = 5
ROOM_MAX = 12
MAX_ENEMIES = 16

# Tiles / symbols
WALL = '#'
FLOOR = '.'
PLAYER_CHAR = '@'
STAIRS = '>'
ENEMY_CHAR = 'g'
POTION = '!'
SWORD = '/'
POWER_SYMBOLS = {'atk': '+', 'hp': 'h', 'def': 'd', 'spd': 's'}
UNKNOWN = ' '

# Colour pair IDs (will be initialized in init_colors)
CP_PLAYER = 1
CP_WALL = 2
CP_FLOOR = 3
CP_ENEMY = 4
CP_POTION = 5
CP_STAIRS = 6
CP_SWORD = 7
CP_POWER = 8
CP_TEXT = 9

class Rect:
	def __init__(self, x, y, w, h):
		self.x1 = x
		self.y1 = y
		self.x2 = x + w
		self.y2 = y + h
	def center(self):
		return ((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)
	def intersect(self, other):
		return (self.x1 <= other.x2 and self.x2 >= other.x1 and
				self.y1 <= other.y2 and self.y2 >= other.y1)

class Entity:
	def __init__(self, x, y, ch, hp=1, name=None):
		self.x = x
		self.y = y
		self.ch = ch
		self.hp = hp
		self.name = name or ch
		# combat stats (for items / actors)
		self.atk = 1
		self.defn = 0

class Item:
	def __init__(self, x, y, ch, kind, name, color_pair=CP_POWER, bonus=1):
		self.x = x
		self.y = y
		self.ch = ch
		self.kind = kind  # 'sword','potion','power'
		self.name = name
		self.color_pair = color_pair
		self.bonus = bonus

class Game:
	def __init__(self, stdscr):
		self.stdscr = stdscr
		self.map = [[WALL for _ in range(MAP_W)] for _ in range(MAP_H)]
		self.rooms = []
		self.player = None
		self.stairs = None
		self.enemies = []
		self.items = []
		self.message = "Welcome — reach '>' to escape. Press 'i' for inventory."
		self.level = 1
		self.make_map()
		self.visible = [[False]*MAP_W for _ in range(MAP_H)]
		self.explored = [[False]*MAP_W for _ in range(MAP_H)]
		self.fov_radius = 12
		self.inventory = []
		self.equipped = None  # index into inventory or None
		self.turn_delay = 0.05

	def create_room(self, room):
		for y in range(room.y1, room.y2):
			for x in range(room.x1, room.x2):
				if 0 <= x < MAP_W and 0 <= y < MAP_H:
					self.map[y][x] = FLOOR

	def create_h_tunnel(self, x1, x2, y):
		for x in range(min(x1,x2), max(x1,x2)+1):
			if 0 <= x < MAP_W and 0 <= y < MAP_H:
				self.map[y][x] = FLOOR

	def create_v_tunnel(self, y1, y2, x):
		for y in range(min(y1,y2), max(y1,y2)+1):
			if 0 <= x < MAP_W and 0 <= y < MAP_H:
				self.map[y][x] = FLOOR

	def make_map(self):
		# procedural rooms
		for _ in range(MAX_ROOMS):
			w = random.randint(ROOM_MIN, ROOM_MAX)
			h = random.randint(ROOM_MIN, ROOM_MAX)
			x = random.randint(1, MAP_W - w - 2)
			y = random.randint(1, MAP_H - h - 2)
			new_room = Rect(x,y,w,h)
			if any(new_room.intersect(other) for other in self.rooms):
				continue
			self.create_room(new_room)
			(cx,cy) = new_room.center()
			if not self.rooms:
				self.player = Entity(cx, cy, PLAYER_CHAR, hp=20, name='You')
				self.player.atk = 2
			else:
				(prevx, prevy) = self.rooms[-1].center()
				if random.choice([True, False]):
					self.create_h_tunnel(prevx, cx, prevy)
					self.create_v_tunnel(prevy, cy, cx)
				else:
					self.create_v_tunnel(prevy, cy, prevx)
					self.create_h_tunnel(prevx, cx, cy)
			self.rooms.append(new_room)

		# place stairs in last room
		last_center = self.rooms[-1].center()
		self.stairs = Entity(last_center[0], last_center[1], STAIRS, name='Stairs')
		# spawn enemies and items
		for _ in range(MAX_ENEMIES):
			room = random.choice(self.rooms)
			x = random.randint(room.x1+1, room.x2-1)
			y = random.randint(room.y1+1, room.y2-1)
			if self.is_blocked(x,y):
				continue
			g = Entity(x,y,ENEMY_CHAR,hp=4, name='Goblin')
			g.atk = 1 + random.randint(0,2)
			g.defn = random.randint(0,1)
			self.enemies.append(g)

		# items: 1 standout sword, some potions, and powerups spread evenly
		# standout sword
		room = random.choice(self.rooms)
		x = random.randint(room.x1+1, room.x2-1)
		y = random.randint(room.y1+1, room.y2-1)
		self.items.append(Item(x, y, SWORD, 'sword', 'Rusty Sword',
							color_pair=CP_SWORD, bonus=3))


		# potions
		for _ in range(6):
			room = random.choice(self.rooms)
			x = random.randint(room.x1+1, room.x2-1)
			y = random.randint(room.y1+1, room.y2-1)
			if self.is_blocked(x,y):
				continue
			self.items.append(Item(x,y,POTION,'potion','Healing Potion',color_pair=CP_POTION,bonus=5))

		# powerups: attack, hp, defense, speed — spread
		kinds = ['atk','hp','def','spd']
		for kind in kinds:
			room = random.choice(self.rooms)
			x = random.randint(room.x1+1, room.x2-1)
			y = random.randint(room.y1+1, room.y2-1)
			if self.is_blocked(x,y):
				continue
			name = {
				'atk':'Bracer of Strength',
				'hp':'Heartstone',
				'def':'Shield Emblem',
				'spd':'Wind Talisman'
			}[kind]
			sym = POWER_SYMBOLS[kind]
			self.items.append(Item(x,y,sym,'power',name,color_pair=CP_POWER,bonus=1))

	def is_blocked(self, x, y):
		if self.map[y][x] == WALL:
			return True
		if self.player and self.player.x == x and self.player.y == y:
			return True
		for e in self.enemies:
			if e.x == x and e.y == y:
				return True
		for it in self.items:
			if it.x == x and it.y == y and it.kind == 'sword':
				# swords block for placement safety
				return True
		return False

	def recompute_fov(self):
		self.visible = [[False]*MAP_W for _ in range(MAP_H)]
		for dy in range(-self.fov_radius, self.fov_radius+1):
			for dx in range(-self.fov_radius, self.fov_radius+1):
				x = self.player.x + dx
				y = self.player.y + dy
				if 0 <= x < MAP_W and 0 <= y < MAP_H:
					if dx*dx + dy*dy <= self.fov_radius*self.fov_radius:
						if self.line_of_sight(self.player.x, self.player.y, x, y):
							self.visible[y][x] = True
							self.explored[y][x] = True

	def line_of_sight(self, x1, y1, x2, y2):
		# Bresenham
		dx = abs(x2 - x1)
		dy = abs(y2 - y1)
		x = x1
		y = y1
		sx = 1 if x2 > x1 else -1
		sy = 1 if y2 > y1 else -1
		if dx > dy:
			err = dx // 2
			while x != x2:
				if self.map[y][x] == WALL and (x,y) != (x1,y1) and (x,y) != (x2,y2):
					return False
				err -= dy
				if err < 0:
					y += sy
					err += dx
				x += sx
		else:
			err = dy // 2
			while y != y2:
				if self.map[y][x] == WALL and (x,y) != (x1,y1) and (x,y) != (x2,y2):
					return False
				err -= dx
				if err < 0:
					x += sx
					err += dy
				y += sy
		return True

	def draw(self):
		self.stdscr.clear()
		# map
		for y in range(MAP_H):
			for x in range(MAP_W):
				ch = UNKNOWN
				attr = curses.color_pair(CP_TEXT)
				if self.visible[y][x]:
					if self.map[y][x] == WALL:
						ch = WALL
						attr = curses.color_pair(CP_WALL)
					else:
						ch = FLOOR
						attr = curses.color_pair(CP_FLOOR)
					# objects
					if self.player.x == x and self.player.y == y:
						ch = PLAYER_CHAR
						attr = curses.color_pair(CP_PLAYER)
					elif self.stairs.x == x and self.stairs.y == y:
						ch = STAIRS
						attr = curses.color_pair(CP_STAIRS)
					else:
						for it in self.items:
							if it.x == x and it.y == y:
								ch = it.ch
								attr = curses.color_pair(it.color_pair)
						for e in self.enemies:
							if e.x == x and e.y == y:
								ch = e.ch
								attr = curses.color_pair(CP_ENEMY)
				elif self.explored[y][x]:
					# dimmed explored
					if self.map[y][x] == WALL:
						ch = WALL
					else:
						ch = ','
				try:
					self.stdscr.addch(y, x, ord(ch), attr)
				except curses.error:
					pass
		# UI panel
		status = f"HP:{self.player.hp}  LV:{self.level}  Enemies:{len(self.enemies)}  Equipped:{self.inventory[self.equipped].name if (self.equipped is not None and self.equipped < len(self.inventory)) else 'None'}  {self.message}"
		try:
			self.stdscr.addstr(MAP_H, 0, status[:MAP_W-1], curses.color_pair(CP_TEXT))
			controls = "Controls: arrows/WASD to move, g wait, i inventory, e equip/cycle, q quit"
			self.stdscr.addstr(MAP_H+1, 0, controls[:MAP_W-1], curses.color_pair(CP_TEXT))
			self.stdscr.refresh()
		except curses.error:
			pass

	def handle_keys(self):
		k = self.stdscr.getch()
		if k == -1:
			return None
		# movement
		if k in (curses.KEY_UP, ord('k'), ord('w'), ord('W')):
			return (0, -1)
		if k in (curses.KEY_DOWN, ord('j'), ord('s'), ord('S')):
			return (0, 1)
		if k in (curses.KEY_LEFT, ord('h'), ord('a'), ord('A')):
			return (-1, 0)
		if k in (curses.KEY_RIGHT, ord('l'), ord('d'), ord('D')):
			return (1, 0)
		if k in (ord('g'), ord('G'), ord(' ')):
			return (0,0)
		if k in (ord('q'), ord('Q')):
			return 'quit'
		if k in (ord('i'), ord('I')):
			self.show_inventory()
			return None
		if k in (ord('e'), ord('E')):
			self.cycle_equip()
			return None
		return None

	def pickup_item_at(self, x, y):
		for it in list(self.items):
			if it.x == x and it.y == y:
				if it.kind == 'potion':
					self.player.hp += it.bonus
					self.message = f"You drink a potion and heal {it.bonus} HP."
					self.items.remove(it)
					return True
				elif it.kind == 'sword':
					# pick up sword into inventory
					self.inventory.append(it)
					self.items.remove(it)
					self.message = f"You pick up {it.name}. Press 'e' to equip."
					return True
				elif it.kind == 'power':
					# apply permanent bonuses spread evenly
					name = it.name
					kind = it.ch
					# map symbol to effect
					if it.ch == POWER_SYMBOLS['atk']:
						self.player.atk += 1
						self.message = f"{name} found — Attack +1 permanently."
					elif it.ch == POWER_SYMBOLS['hp']:
						self.player.hp += 3
						self.message = f"{name} found — Max HP +3 (healed)."
					elif it.ch == POWER_SYMBOLS['def']:
						self.player.defn += 1
						self.message = f"{name} found — Defence +1 permanently."
					elif it.ch == POWER_SYMBOLS['spd']:
						# speed gives a small temporary heal and message
						self.player.hp += 2
						self.message = f"{name} found — You feel swift! (+2 HP)"
					self.items.remove(it)
					return True
		return False

	def move_player(self, dx, dy):
		nx = self.player.x + dx
		ny = self.player.y + dy
		if not (0 <= nx < MAP_W and 0 <= ny < MAP_H):
			self.message = "You bump the edge of the map."
			return
		if self.map[ny][nx] == WALL:
			self.message = "You hit a wall."
			return
		# check enemy
		target = None
		for e in self.enemies:
			if e.x == nx and e.y == ny:
				target = e
				break
		if target:
			# attack (classic bump-to-attack)
			dmg = random.randint(1,3) + self.player.atk
			# weapon bonus if equipped
			if self.equipped is not None and self.equipped < len(self.inventory):
				itm = self.inventory[self.equipped]
				if itm.kind == 'sword':
					dmg += itm.bonus
			# enemy defence reduces damage
			actual = max(0, dmg - target.defn)
			target.hp -= actual
			self.message = f"You hit {target.name} for {actual}!"
			if target.hp <= 0:
				self.enemies.remove(target)
				self.message = f"You slay the {target.name}!"
			return
		# check items
		if self.pickup_item_at(nx, ny):
			# player moves onto item tile if not potion
			if any(it.x == nx and it.y == ny for it in self.items):
				self.player.x = nx
				self.player.y = ny
			return
		# check stairs
		if self.stairs.x == nx and self.stairs.y == ny:
			self.level_up()
			return
		# empty floor
		self.player.x = nx
		self.player.y = ny
		self.message = "You move."

	def enemy_turns(self):
		for e in list(self.enemies):
			# simple AI: move toward player if visible, else wander
			if abs(e.x - self.player.x) <= self.fov_radius and abs(e.y - self.player.y) <= self.fov_radius:
				if self.visible[e.y][e.x] and self.line_of_sight(e.x, e.y, self.player.x, self.player.y):
					dx = 1 if self.player.x > e.x else -1 if self.player.x < e.x else 0
					dy = 1 if self.player.y > e.y else -1 if self.player.y < e.y else 0
					nx = e.x + dx
					ny = e.y + dy
					# attack if on player
					if nx == self.player.x and ny == self.player.y:
						damage = random.randint(1,3) + (e.atk if hasattr(e, 'atk') else 1)
						# defence reduces
						actual = max(0, damage - self.player.defn)
						self.player.hp -= actual
						self.message = f"A {e.name} hits you for {actual}!"
						if self.player.hp <= 0:
							self.game_over("You were slain.")
							return
					elif not self.is_blocked(nx, ny):
						e.x = nx
						e.y = ny
			else:
				# random move
				if random.random() < 0.25:
					dx, dy = random.choice([(1,0),(-1,0),(0,1),(0,-1),(0,0)])
					nx = e.x + dx
					ny = e.y + dy
					if (0 <= nx < MAP_W and 0 <= ny < MAP_H and
						self.map[ny][nx] != WALL and not self.is_blocked(nx, ny)):
						e.x = nx
						e.y = ny

	def game_over(self, msg):
		self.draw()
		self.stdscr.addstr(MAP_H//2, MAP_W//2 - len(msg)//2, msg)
		self.stdscr.addstr(MAP_H//2+1, MAP_W//2 - 8, "Press any key to quit.")
		self.stdscr.refresh()
		self.stdscr.getch()
		curses.endwin()
		print(msg)
		sys.exit(0)

	def level_up(self):
		self.level += 1
		self.player.hp = min(50, self.player.hp + 8)
		self.message = "You descend deeper... the dungeon reshapes!"
		# regenerate map with stronger enemies
		self.map = [[WALL for _ in range(MAP_W)] for _ in range(MAP_H)]
		self.rooms = []
		self.enemies = []
		self.items = []
		self.make_map()
		self.player.x, self.player.y = self.rooms[0].center()
		for e in self.enemies:
			e.hp += self.level // 2

	def show_inventory(self):
		# simple inventory display; press any key to close
		h = 10
		w = 40
		sy = max(0, MAP_H//2 - h//2)
		sx = max(0, MAP_W//2 - w//2)
		win = curses.newwin(h, w, sy, sx)
		win.border()
		win.addstr(0, 2, " Inventory ")
		if not self.inventory:
			win.addstr(2, 2, "(empty)")
		else:
			for i, it in enumerate(self.inventory):
				mark = '*' if self.equipped == i else ' '
				win.addstr(2+i, 2, f"{mark} [{i}] {it.name} ({it.kind})")
		win.addstr(h-2, 2, "Press number to equip, any other key to close.")
		win.refresh()
		c = win.getch()
		if c >= ord('0') and c <= ord('9'):
			n = c - ord('0')
			if n < len(self.inventory):
				self.equipped = n
				self.message = f"Equipped {self.inventory[n].name}."
		win.erase()
		del win

	def cycle_equip(self):
		if not self.inventory:
			self.message = "No items to equip."
			return
		if self.equipped is None:
			self.equipped = 0
		else:
			self.equipped = (self.equipped + 1) % len(self.inventory)
		self.message = f"Equipped {self.inventory[self.equipped].name}."

	def main_loop(self):
		self.stdscr.nodelay(False)
		while True:
			self.recompute_fov()
			self.draw()
			action = None
			while action is None:
				action = self.handle_keys()
			if action == 'quit':
				self.game_over("You quit. Bye!")
			dxdy = action
			if dxdy == (0,0):
				self.message = "You wait..."
			else:
				self.move_player(dxdy[0], dxdy[1])
			# enemies move
			self.enemy_turns()
			# check win
			if self.player.x == self.stairs.x and self.player.y == self.stairs.y:
				self.level_up()
			# check alive
			if self.player.hp <= 0:
				self.game_over("You died.")

def init_colors():
	# init colours and pairs
	if not curses.has_colors():
		return
	curses.start_color()
	curses.use_default_colors()
	curses.init_pair(CP_PLAYER, curses.COLOR_YELLOW, -1)
	curses.init_pair(CP_WALL, curses.COLOR_WHITE, -1)
	curses.init_pair(CP_FLOOR, curses.COLOR_BLACK, -1)
	curses.init_pair(CP_ENEMY, curses.COLOR_GREEN, -1)
	curses.init_pair(CP_POTION, curses.COLOR_RED, -1)
	curses.init_pair(CP_STAIRS, curses.COLOR_CYAN, -1)
	curses.init_pair(CP_SWORD, curses.COLOR_MAGENTA, -1)
	curses.init_pair(CP_POWER, curses.COLOR_BLUE, -1)
	curses.init_pair(CP_TEXT, curses.COLOR_WHITE, -1)

def main(stdscr):
	# curses setup
	curses.curs_set(0)
	stdscr.keypad(True)
	stdscr.timeout(100)
	init_colors()
	game = Game(stdscr)
	game.main_loop()

if __name__ == "__main__":
	try:
		curses.wrapper(main)
	except KeyboardInterrupt:
		print("Bye.")
