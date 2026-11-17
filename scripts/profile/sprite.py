"""Pixel raccoon sprite parts. Every part is a dict of (x, y) -> color in sprite pixels."""
import math, random, json
W, H, GROUND = 212, 124, 66

def ell(cx, cy, rx, ry):
    return {(x, y) for x in range(int(cx - rx) - 1, int(cx + rx) + 2) for y in range(int(cy - ry) - 1, int(cy + ry) + 2)
            if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1}
def tri(p):
    (x1, y1), (x2, y2), (x3, y3) = p; s = set(); d = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
    for x in range(int(min(x1, x2, x3)), int(max(x1, x2, x3)) + 1):
        for y in range(int(min(y1, y2, y3)), int(max(y1, y2, y3)) + 1):
            a = ((y2 - y3) * (x + .5 - x3) + (x3 - x2) * (y + .5 - y3)) / d
            b = ((y3 - y1) * (x + .5 - x3) + (x1 - x3) * (y + .5 - y3)) / d
            if a >= 0 and b >= 0 and 1 - a - b >= 0: s.add((x, y))
    return s
def outline(cells, color='#1b1c22'):
    o = {}
    for (x, y) in cells:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in cells: o[n] = color
    return o

F = ['#5a6069', '#6d747e', '#838a94', '#9ba1aa', '#b3b9c0', '#c9ced4']  # fur dark->light
C = dict(out='#1b1c22', dark0='#25262c', dark1='#33353c', dark2='#43464e', white0='#dfe2e6', white1='#f1f3f5', white2='#ffffff',
         pink='#e8a3ab', pinkd='#b97c84', nose='#15161b', eye0='#141626', eye1='#232843', eye2='#38406a', shine='#ffffff',
         belly='#c3c8ce', paw='#383a41', pawl='#50535b', blush='#ff8fa3', whisk='#eef0f2', mouth='#2a1f24', tongue='#f07a8a')

def tone(l):
    return F[max(0, min(5, int(l * 6)))]

def body_part():
    cx, cy, rx, ry = 112, GROUND, 50, 31
    cells = {p for p in ell(cx, cy, rx, ry) if p[1] < GROUND}
    px = {}
    random.seed(3)
    for (x, y) in cells:
        nx = (x + .5 - cx) / rx; ny = (y + .5 - cy) / ry
        l = 0.62 - 0.55 * nx * 0.6 - 0.75 * ny * 0.9
        d = math.hypot(nx, ny)
        if d > 0.9: l -= 0.18
        px[(x, y)] = tone(l)
        if x < 92 and y > GROUND - 9: px[(x, y)] = C['belly'] if y > GROUND - 6 else F[4]
    for _ in range(140):
        x = random.randint(70, 158); y = random.randint(GROUND - 28, GROUND - 3)
        if (x, y) in px and (x + 1, y - 1) in px:
            i = F.index(px[(x, y)]) if px[(x, y)] in F else 3
            c = F[max(0, i - 1)]
            px[(x, y)] = c; px[(x + 1, y - 1)] = c
            if random.random() < .4 and (x + 2, y - 2) in px: px[(x + 2, y - 2)] = c
    out = outline(set(px))
    out = {k: v for k, v in out.items() if k[1] < GROUND}
    return px, out, (cx, GROUND)

HC = (44, 40)  # head center
def head_part():
    hx, hy = HC
    head = ell(hx, hy, 29, 24.5) | tri([(hx - 30, hy + 2), (hx - 33, hy + 14), (hx - 20, hy + 13)]) | tri([(hx + 30, hy + 2), (hx + 33, hy + 14), (hx + 20, hy + 13)])
    head |= ell(hx, hy + 13, 22, 9)
    px = {}
    for (x, y) in head:
        nx = (x + .5 - hx) / 29; ny = (y + .5 - hy) / 24
        px[(x, y)] = tone(0.7 - 0.25 * nx - 0.55 * ny)
    stripe = {(x, y) for y in range(hy - 25, hy - 6) for x in range(hx - 2 + (0 if y > hy - 16 else 0), hx + 2)} | ell(hx, hy - 6, 3, 2.5)
    for p in stripe:
        if p in head: px[p] = C['dark1']
    mask = ell(hx - 13, hy + 0.5, 12, 8) | ell(hx + 13, hy + 0.5, 12, 8) | {(x, y) for x in range(hx - 4, hx + 4) for y in range(hy - 3, hy + 2)}
    for p in mask:
        if p in head: px[p] = C['dark0'] if p[1] > hy - 5 else C['dark1']
    for p in ell(hx, hy + 13, 13, 9) | ell(hx, hy + 18, 10, 4):
        if p in px: px[p] = C['white0']
    out = outline(set(px))
    return px, out, (hx, hy + 22)

def brow_part(side):
    hx, hy = HC; s = -1 if side == 'L' else 1
    return {p: C['white1'] for p in ell(hx + s * 13, hy - 9.5, 9, 3.6)}, (hx + s * 13, hy - 9.5)

MUZ = (HC[0], HC[1] + 12)
def muzzle_part():
    hx, hy = HC; m = {}
    for p in ell(hx, hy + 11, 12, 8.5) | ell(hx, hy + 17, 9, 4): m[p] = C['white1'] if p[1] < hy + 15 else C['white0']
    for p in outline(set(m), '#c4c9cf'):
        if p[1] > hy + 13: m[p] = '#c4c9cf'
    return m

def nose_part():
    hx, hy = HC; n = {}
    for p in ell(hx, hy + 6.6, 3.8, 2.6): n[p] = C['nose']
    n[(hx - 2, hy + 5)] = '#5a5b66'; n[(hx - 1, hy + 5)] = '#3a3b44'
    return n, (hx, hy + 7)

def ear_part(side):
    hx, hy = HC
    s = -1 if side == 'L' else 1
    base1, base2, apex = (hx + s * 9, hy - 18), (hx + s * 27, hy - 10), (hx + s * 24, hy - 33)
    cells = tri([base1, base2, apex]) | ell(hx + s * 20, hy - 16, 8, 6)
    px = {}
    for p in cells: px[p] = F[3] if p[1] > hy - 24 else F[2]
    inner = tri([(hx + s * 13, hy - 18), (hx + s * 24, hy - 13), (hx + s * 22.5, hy - 28)])
    for p in inner: px[p] = C['pink'] if p[1] > hy - 22 else C['pinkd']
    for p in [(int(hx + s * 24), hy - 33), (int(hx + s * 24), hy - 34)]: px[p] = C['dark1']
    out = outline(set(px))
    pivot = ((base1[0] + base2[0]) / 2, (base1[1] + base2[1]) / 2)
    return px, out, pivot

EYE = {'L': (HC[0] - 13, HC[1] + 0), 'R': (HC[0] + 13, HC[1] + 0)}
def eye_part(side, kind):
    ex, ey = EYE[side]
    px = {}
    if kind == 'open':
        for p in ell(ex, ey, 6.2, 7.2): px[p] = '#0e1020'
        for p in ell(ex, ey + 0.6, 5.0, 6.0):
            t = (p[1] - (ey - 5.4)) / 12
            px[p] = '#2a3368' if t < 0.35 else '#3d4c95' if t < 0.62 else '#5f74c9' if t < 0.85 else '#8aa0ea'
        for p in ell(ex, ey + 0.8, 2.6, 3.2): px[p] = '#0a0b16'
        for p in ell(ex - 2.0, ey - 2.6, 2.1, 2.1): px[p] = C['shine']
        px[(int(ex + 2), int(ey + 3))] = C['shine']; px[(int(ex + 3), int(ey + 2))] = '#dfe5ff'; px[(int(ex + 1), int(ey + 4))] = '#c9d2ff'
    elif kind == 'big':
        for p in ell(ex, ey, 7.0, 8.0): px[p] = '#0e1020'
        for p in ell(ex, ey + 0.5, 5.8, 6.8):
            t = (p[1] - (ey - 6.3)) / 13.6
            px[p] = '#2a3368' if t < 0.35 else '#3d4c95' if t < 0.62 else '#5f74c9' if t < 0.85 else '#8aa0ea'
        for p in ell(ex, ey + 0.8, 3.2, 3.8): px[p] = '#0a0b16'
        for p in ell(ex - 2.3, ey - 3.0, 2.5, 2.5): px[p] = C['shine']
        for p in ell(ex + 2.6, ey + 3.2, 1.2, 1.2): px[p] = C['shine']
        px[(int(ex + 3), int(ey - 2))] = '#dfe5ff'
    elif kind == 'squint':
        for p in ell(ex, ey, 6.2, 7.2):
            if p[1] <= ey + 1: px[p] = '#0e1020'
        for p in ell(ex, ey + 0.6, 5.0, 6.0):
            if p[1] <= ey + 0:
                t = (p[1] - (ey - 5.4)) / 6
                px[p] = '#2a3368' if t < 0.5 else '#4a5cb0'
        for p in ell(ex - 2.0, ey - 2.8, 1.8, 1.8): px[p] = C['shine']
        for dx in range(-6, 7):
            dy = round(-((6.4 ** 2 - dx * dx) ** .5) * 0.32) + 2
            px[(ex + dx, ey + dy)] = '#9aa0a8'; px[(ex + dx, ey + dy + 1)] = '#b3b9c0'
    elif kind == 'happy':
        for dx in range(-5, 6):
            dy = round(-((5.2 ** 2 - dx * dx) ** .5) * 0.55) + 2
            px[(ex + dx, ey + dy)] = C['white2']; px[(ex + dx, ey + dy + 1)] = C['white1']
    elif kind == 'closed':
        for dx in range(-5, 6):
            dy = round(((5.2 ** 2 - dx * dx) ** .5) * 0.45)
            px[(ex + dx, ey + dy)] = '#9aa0a8'; 
    elif kind == 'half':
        for p in ell(ex, ey + 1.5, 5.6, 4.6):
            if p[1] >= ey: px[p] = C['eye0'] if p[1] < ey + 3 else C['eye1']
        for dx in range(-5, 6): px[(ex + dx, ey - 0)] = '#8d939b'; px[(ex + dx, ey - 1)] = '#6d727a'
        px[(ex + 2, ey + 2)] = C['shine']
    return px

def mouth_part(kind):
    hx, hy = HC; m = {}
    if kind == 'smile':
        for p in [(hx, hy + 9), (hx, hy + 10), (hx - 1, hy + 11), (hx - 2, hy + 11), (hx - 3, hy + 10), (hx + 1, hy + 11), (hx + 2, hy + 11), (hx + 3, hy + 10)]: m[p] = C['mouth']
    elif kind == 'open':
        for p in [(hx, hy + 9)]: m[p] = C['mouth']
        for p in ell(hx, hy + 12, 3.6, 2.8): m[p] = C['mouth']
        for p in ell(hx, hy + 13.4, 2.4, 1.4): m[p] = C['tongue']
    elif kind == 'yawn':
        for p in ell(hx, hy + 13, 4.4, 4.6): m[p] = C['mouth']
        for p in ell(hx, hy + 15, 3, 1.8): m[p] = C['tongue']
        m[(hx - 2, hy + 9)] = C['white2']; m[(hx + 2, hy + 9)] = C['white2']
    elif kind == 'sleep':
        for p in [(hx, hy + 9), (hx - 1, hy + 10), (hx + 1, hy + 10)]: m[p] = C['mouth']
    elif kind == 'grin':
        m[(hx, hy + 9)] = C['mouth']
        for p in ell(hx, hy + 11.5, 6.2, 4.6):
            if p[1] >= hy + 10: m[p] = C['mouth']
        for p in ell(hx, hy + 14, 3.6, 1.8): m[p] = C['tongue']
        for x in range(hx - 4, hx + 5): m[(x, hy + 10)] = C['white2']
        m[(hx - 7, hy + 9)] = C['mouth']; m[(hx + 6, hy + 9)] = C['mouth']
    elif kind == 'w':
        for p in [(hx, hy + 9), (hx, hy + 10), (hx - 1, hy + 11), (hx - 2, hy + 11), (hx - 3, hy + 11), (hx - 4, hy + 10), (hx + 1, hy + 11), (hx + 2, hy + 11), (hx + 3, hy + 11), (hx + 4, hy + 10), (hx - 5, hy + 9), (hx + 5, hy + 9)]: m[p] = C['mouth']
    elif kind == 'o':
        m[(hx, hy + 9)] = C['mouth']
        for p in ell(hx, hy + 12, 1.9, 2.1): m[p] = C['mouth']
    return m

def blush_part(side):
    hx, hy = HC; s = -1 if side == 'L' else 1
    return {p: C['blush'] for p in ell(hx + s * 20, hy + 9, 4.6, 2.4)}, (hx + s * 20, hy + 9)

def whisker_part(side):
    hx, hy = HC; s = -1 if side == 'L' else 1; w = {}
    for row, dy in enumerate((-1, 1, 3)):
        for i in range(7):
            w[(hx + s * (12 + i), hy + 11 + dy + (i * (row - 1)) // 4)] = C['whisk']
    return w, (hx + s * 12, hy + 12)

def paws_part():
    px = {}
    for cx in (HC[0] - 12, HC[0] + 12):
        for p in ell(cx, GROUND - 2.5, 7.5, 4.2):
            if p[1] < GROUND: px[p] = C['pawl'] if p[1] < GROUND - 3 else C['paw']
        for dx in (-3, 0, 3): px[(cx + dx, GROUND - 1)] = C['out']; px[(cx + dx, GROUND - 2)] = C['out']
    out = {k: v for k, v in outline(set(px)).items() if k[1] < GROUND}
    return px, out

TAIL_BASE = (148, 47)
TAIL_LEN = 5.0
TAIL_R = [11, 12, 12.5, 12.8, 12.8, 12.5, 12.2, 11.8, 11.3, 10.8, 10.2, 9.5, 8.6, 7.6, 6.4]
TAIL_ANG = [-12, 6, 9, 12, 14, 14, 12, 10, 8, 6, 4, 3, 2, 1, 1]
TAIL_PATTERN = ['F', 'F', 'D', 0, 0, 'D', 1, 1, 'D', 2, 2, 'D', 3, 'D', 'D']
def tail_blob(r):
    random.seed(int(r * 100))
    cells = ell(0, 0, r, r * 1.04)
    for k in range(18):
        a = k / 18 * math.tau + random.uniform(-.12, .12)
        ln = random.choice([1, 1, 2, 2])
        for j in range(1, ln + 1):
            x = round(math.cos(a) * (r + j - .5)); y = round(math.sin(a) * (r * 1.04 + j - .5))
            cells.add((x, y))
            if j < ln: cells.add((x + (1 if math.cos(a) > 0 else -1), y))
    shade = {}
    for (x, y) in cells:
        v = (y + .5) / r; u = (x + .5) / r
        s = 0 if v < -0.4 + 0.2 * u else 2 if v > 0.5 else 1
        shade[(x, y)] = s
    for _ in range(int(r * 1.6)):
        x = random.randint(int(-r) + 2, int(r) - 2); y = random.randint(int(-r) + 2, int(r) - 2)
        if (x, y) in shade and (x + 1, y - 1) in shade:
            s = max(0, shade[(x, y)] - 1); shade[(x, y)] = s; shade[(x + 1, y - 1)] = s
    out = outline(set(shade))
    return shade, out

def leaf(x, y, a, b, flip=False):
    pts = [(1, 0, a), (2, 0, a), (0, 1, a), (1, 1, b), (2, 1, a), (3, 1, a), (1, 2, a), (2, 2, b), (3, 2, a), (2, 3, a), (4, 2, b)]
    return [((x - dx) if flip else (x + dx), y + dy, c) for dx, dy, c in pts]

SEASON_COLORS = {'spring': ('#f6a6c1', '#ffe08a', '#f9c6d6'), 'summer': ('#6bcb5a', '#2f8f3f', '#9be36d'), 'autumn': ('#e8752a', '#9a3412', '#f2b04a')}
def season_parts(season, body):
    hx, hy = HC
    tops = {}
    for (x, y) in body: tops[x] = min(tops.get(x, 999), y)
    head, bod = [], []
    if season == 'winter':
        for x in range(hx - 20, hx + 21):
            y = round(hy - 24.5 * (1 - ((x - hx) / 29) ** 2) ** .5) - 1
            head.append((x, y, '#ffffff')); head.append((x, y + 1, '#ffffff' if abs(x - hx) < 16 else '#e3eaf2'))
        head += leaf(hx + 4, hy - 30, '#2f6f3a', '#1f4f2a') + leaf(hx - 4, hy - 30, '#2f6f3a', '#1f4f2a', flip=True)
        head += [(hx, hy - 28, '#d83a3a'), (hx + 1, hy - 28, '#d83a3a'), (hx - 1, hy - 27, '#e85a5a'), (hx + 1, hy - 26, '#c82a2a')]
        for x in range(72, 152):
            if x in tops:
                bod.append((x, tops[x] - 1, '#ffffff'))
                if x % 4: bod.append((x, tops[x], '#eef3f8'))
                if x % 6 == 0: bod.append((x, tops[x] - 2, '#ffffff'))
    else:
        a, b, c = SEASON_COLORS[season]
        head = leaf(hx - 9, hy - 28, a, b) + leaf(hx + 2, hy - 30, c, b) + leaf(hx + 8, hy - 27, a, b)
        for x0, col in ((92, a), (104, c), (118, a), (132, c)):
            bod += leaf(x0, tops[x0 + 2] - 3, col, b)
    return head, bod

HOLIDAYS = ['none', 'halloween', 'thanksgiving', 'christmas', 'newyear', 'lunarnewyear', 'valentines', 'birthday']
def holiday_parts(h):
    hx, hy = HC
    head, front = [], []
    def box(L, x0, y0, x1, y1, c):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1): L.append((x, y, c))
    if h == 'halloween':
        for y in range(hy - 50, hy - 20):
            half = max(1, (y - (hy - 50)) // 2.6)
            for x in range(int(hx + 4 - half), int(hx + 5 + half)): head.append((x, y, '#3b2a52' if (x * 3 + y) % 7 else '#523e70'))
        box(head, hx - 24, hy - 21, hx + 30, hy - 19, '#2b1f3d'); box(head, hx - 6, hy - 24, hx + 15, hy - 22, '#e8752a')
        for p in ell(84, GROUND - 5, 6.5, 5.2): front.append((p[0], p[1], '#e8752a' if (p[0] % 4) else '#c85a1a'))
        front += [(84, GROUND - 11, '#3f7a3a'), (84, GROUND - 12, '#3f7a3a'), (85, GROUND - 12, '#3f7a3a'), (82, GROUND - 6, '#2a1a0a'), (86, GROUND - 6, '#2a1a0a'), (83, GROUND - 3, '#2a1a0a'), (84, GROUND - 3, '#2a1a0a'), (85, GROUND - 3, '#2a1a0a')]
    elif h == 'thanksgiving':
        for p in ell(hx, hy - 17, 19, 11):
            if p[1] <= hy - 17: head.append((p[0], p[1], '#e8752a' if (p[0] + p[1]) % 4 else '#f39550'))
        box(head, hx - 20, hy - 19, hx + 20, hy - 15, '#c8402a')
        for x in range(hx - 19, hx + 20, 2): head.append((x, hy - 17, '#a8321f'))
        for p in ell(hx, hy - 30, 3.5, 3.2): head.append((p[0], p[1], '#f2b04a' if (p[0] + p[1]) % 2 else '#ffd27a'))
        for p in ell(84, GROUND - 3.5, 8, 3.6): front.append((p[0], p[1], '#e2ad66' if p[1] < GROUND - 4 else '#b07a3a'))
        for x in range(78, 91, 3): front.append((x, GROUND - 6, '#f6e2c0'))
        box(front, 76, GROUND - 1, 92, GROUND - 1, '#8a5a2a')
    elif h == 'christmas':
        for y in range(hy - 44, hy - 18):
            w = (y - (hy - 44)) // 1.7 + 2
            for x in range(int(hx + 10 - w), int(hx + 10 + w)): head.append((x, y, '#c62a2a' if (x + y) % 9 else '#e04444'))
        box(head, hx - 22, hy - 21, hx + 24, hy - 17, '#ffffff')
        for p in ell(hx + 14, hy - 46, 3.6, 3.6): head.append((p[0], p[1], '#ffffff'))
    elif h in ('newyear', 'birthday'):
        cols = ['#ff6a2b', '#ffd34d', '#7c9cff', '#e86bff'] if h == 'newyear' else ['#e86bff', '#9be36d', '#ffd34d', '#7c9cff']
        for y in range(hy - 50, hy - 20):
            half = (y - (hy - 50)) // 4
            for x in range(hx - half, hx + 1 + half): head.append((x, y, cols[(y // 4) % 4]))
        for p in ell(hx, hy - 51, 3, 3): head.append((p[0], p[1], '#ffffff'))
    elif h == 'lunarnewyear':
        box(head, hx + 27, hy - 30, hx + 27, hy - 20, '#2b2b2b')
        for p in ell(hx + 27.5, hy - 13, 6, 7): head.append((p[0], p[1], '#d82a2a' if p[0] % 3 else '#b81f1f'))
        box(head, hx + 23, hy - 20, hx + 32, hy - 20, '#f2c14a'); box(head, hx + 23, hy - 6, hx + 32, hy - 6, '#f2c14a'); box(head, hx + 27, hy - 5, hx + 28, hy, '#f2c14a')
    elif h == 'valentines':
        pass
    return head, front

