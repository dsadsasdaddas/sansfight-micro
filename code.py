# SansFight micro — T-Dongle S3 (CircuitPython)
# Core of SansFight's "blue-heart gravity + bone-gap dodge", one-button, 160x80.
# Red soul falls under gravity; tap button = thrust up. White bone walls scroll
# left with a gap; fly through the gap, avoid the bones.
import board, displayio, digitalio, time, terminalio, random
from displayio import Bitmap, Palette, TileGrid, Group
from adafruit_display_text import label

display = board.DISPLAY
display.brightness = 0          # backlight ON (active-low on T-Dongle S3)
W, H = display.width, display.height
FONT = terminalio.FONT

RED, WHITE, BLACK, YELLOW = 0xFF0000, 0xFFFFFF, 0x000000, 0xFFFF00

# ---- input: GPIO0 button (active-low) ----
btn = digitalio.DigitalInOut(board.IO0)
btn.direction = digitalio.Direction.INPUT
btn.pull = digitalio.Pull.UP

# ---- heart sprite 7x6 ----
def heart_grid():
    bmp = Bitmap(7, 6, 2)
    pal = Palette(2); pal[0] = BLACK; pal.make_transparent(0); pal[1] = RED
    rows = [".XX.XX.", "XXXXXXX", "XXXXXXX", ".XXXXX.", "..XXX..", "...X..."]
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c == 'X':
                bmp[x, y] = 1
    return TileGrid(bmp, pixel_shader=pal)

BAR_W = 7
def make_wall(gap_y, gap_h):
    g = Group()
    pal = Palette(1); pal[0] = WHITE
    if gap_y > 0:
        g.append(TileGrid(Bitmap(BAR_W, gap_y, 1), pixel_shader=pal, x=0, y=0))
    bh = H - (gap_y + gap_h)
    if bh > 0:
        g.append(TileGrid(Bitmap(BAR_W, bh, 1), pixel_shader=pal, x=0, y=gap_y + gap_h))
    return g

# ---- scene ----
root = Group()
display.root_group = root
bp = Palette(1); bp[0] = WHITE
def bar(x, y, w, h):
    root.append(TileGrid(Bitmap(max(w, 1), max(h, 1), 1), pixel_shader=bp, x=x, y=y))
bar(0, 0, W, 1); bar(0, H - 1, W, 1); bar(0, 0, 1, H); bar(W - 1, 0, 1, H)

score_lbl = label.Label(FONT, text="0", color=YELLOW, x=W - 12, y=5)
root.append(score_lbl)
state_lbl = label.Label(FONT, text="", color=WHITE, x=6, y=5)
root.append(state_lbl)
heart = heart_grid()
root.append(heart)

HX = 26
GAP_H = 30
GRAVITY = 200.0
THRUST = 480.0
MAX_VY = 110.0
SPAWN_GAP = 72

hy = H / 2.0
vy = 0.0
walls = []
score = 0
lives = 3
invuln = 0.0
spawn_x = W + 20.0
speed = 48.0
state = "MENU"

def clear_walls():
    for w in walls:
        if w['g'] in root:
            root.remove(w['g'])
    walls.clear()

def reset_game():
    global hy, vy, score, lives, invuln, spawn_x, speed
    clear_walls()
    hy = H / 2.0; vy = 0.0
    score = 0; lives = 3; invuln = 0.0
    spawn_x = W + 20.0; speed = 40.0
    score_lbl.text = "0"

def spawn_wall(x):
    gap_y = random.randint(6, H - GAP_H - 6)
    g = make_wall(gap_y, GAP_H)
    g.x = int(x)
    root.append(g)
    walls.append({'g': g, 'x': x, 'gap_y': gap_y, 'gap_h': GAP_H, 'scored': False})

prev_btn = False
last = time.monotonic()

while True:
    now = time.monotonic()
    dt = now - last
    last = now
    if dt > 0.1:
        dt = 0.1
    cur = not btn.value
    pressed = cur and not prev_btn
    prev_btn = cur

    if state == "MENU":
        state_lbl.text = "SansFight"
        hy = H / 2.0 + 6 * (1 - 2 * ((now * 0.8) % 1))
        heart.hidden = False
        heart.x = HX; heart.y = int(hy)
        if pressed:
            reset_game()
            state = "PLAY"
            state_lbl.text = ""
    elif state == "PLAY":
        if cur:                       # HOLD button to rise (no rapid tapping)
            vy -= THRUST * dt
        vy += GRAVITY * dt
        if vy > MAX_VY: vy = MAX_VY
        if vy < -MAX_VY: vy = -MAX_VY
        hy += vy * dt
        if hy < 2: hy = 2; vy = 0
        if hy > H - 8: hy = H - 8; vy = 0

        spawn_x -= speed * dt
        if spawn_x <= W - SPAWN_GAP:
            spawn_wall(W + 2)
            spawn_x += SPAWN_GAP
            speed = min(speed + 1.0, 80.0)

        hit = False
        for w in walls:
            w['x'] -= speed * dt
            w['g'].x = int(w['x'])
            if not w['scored'] and w['x'] + BAR_W < HX:
                w['scored'] = True
                score += 1
                score_lbl.text = str(score)
            if invuln <= 0:
                if w['x'] < HX + 6 and w['x'] + BAR_W > HX + 1:
                    gy0 = w['gap_y']; gy1 = w['gap_y'] + w['gap_h']
                    if not (hy + 1 >= gy0 and hy + 5 <= gy1):
                        hit = True
        for w in list(walls):
            if w['x'] < -BAR_W - 2:
                if w['g'] in root:
                    root.remove(w['g'])
                walls.remove(w)
        if hit:
            lives -= 1
            invuln = 1.2
            if lives <= 0:
                state = "OVER"
                state_lbl.text = "OVER " + str(score)
        heart.x = HX; heart.y = int(hy)
    elif state == "OVER":
        if pressed:
            reset_game()
            state = "PLAY"
            state_lbl.text = ""

    if state == "PLAY" and invuln > 0:
        invuln -= dt
        heart.hidden = (int(invuln * 10) % 2 == 0)
    else:
        heart.hidden = False
