"""Draws the whole profile README as one animated SVG (SMIL, plays inside GitHub READMEs)."""
import math
from xml.sax.saxutils import escape

import sprite as S
import motion as MO

WIDTH = 820
SANS = "'Inter','Segoe UI','Helvetica Neue',Arial,sans-serif"
MONO = "'SFMono-Regular','JetBrains Mono',Menlo,Consolas,monospace"
PX = 3
RACC_X, RACC_Y = 200, 72

LANG_COLORS = {
    'TypeScript': '#3178c6', 'JavaScript': '#f1e05a', 'Python': '#3572a5', 'Java': '#b07219', 'CSS': '#663399',
    'HTML': '#e34c26', 'Go': '#00add8', 'Shell': '#89e051', 'SQL': '#e38c00', 'PLpgSQL': '#336790', 'Rust': '#dea584',
    'C++': '#f34b7d', 'C': '#555555', 'C#': '#178600', 'Kotlin': '#a97bff', 'Swift': '#f05138', 'Ruby': '#701516',
    'PHP': '#4f5d95', 'Jupyter Notebook': '#da5b0b', 'Vue': '#41b883', 'Svelte': '#ff3e00', 'Dart': '#00b4ab',
    'SCSS': '#c6538c', 'Dockerfile': '#384d54', 'Lua': '#000080', 'R': '#198ce7', 'MDX': '#fcb32c', 'Astro': '#ff5a03',
}


def shade(hex_, f):
    h = hex_.lstrip('#')
    v = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    return '#' + ''.join('%02x' % round(c + (255 - c) * f if f >= 0 else c * (1 + f)) for c in v)


def pix(cells):
    """cells: iterable of (x, y, color) -> SVG paths, one per color, horizontal runs merged."""
    by = {}
    for x, y, c in cells:
        by.setdefault(c, set()).add((x, y))
    out = []
    for c, pts in by.items():
        rows = {}
        for x, y in pts:
            rows.setdefault(y, []).append(x)
        d = []
        for y in sorted(rows):
            xs = sorted(rows[y])
            start = prev = xs[0]
            for x in xs[1:] + [None]:
                if x is not None and x == prev + 1:
                    prev = x
                    continue
                d.append(f'M{start} {y}h{prev - start + 1}v1h-{prev - start + 1}z')
                if x is not None:
                    start = prev = x
        out.append(f'<path fill="{c}" d="{"".join(d)}"/>')
    return ''.join(out)


def items(d):
    return [(x, y, c) for (x, y), c in d.items()]


def num(v):
    s = f'{v:.2f}'.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


class Anim:
    def __init__(self, dur):
        self.dur = dur

    def _common(self, begin=None):
        b = f' begin="{num(begin)}s"' if begin else ''
        return f'dur="{num(self.dur)}s" repeatCount="indefinite"{b}'

    def rotate(self, vals, cx=0, cy=0, additive=False, begin=None):
        v = ';'.join(f'{num(a)} {num(cx)} {num(cy)}' for a in vals)
        add = ' additive="sum"' if additive else ''
        return f'<animateTransform attributeName="transform" type="rotate" values="{v}" {self._common(begin)}{add}/>'

    def translate(self, vals, additive=False, begin=None):
        v = ';'.join(f'{num(x)} {num(y)}' for x, y in vals)
        add = ' additive="sum"' if additive else ''
        return f'<animateTransform attributeName="transform" type="translate" values="{v}" {self._common(begin)}{add}/>'

    def scale(self, vals, additive=False, begin=None):
        v = ';'.join(f'{num(x)} {num(y)}' for x, y in vals)
        add = ' additive="sum"' if additive else ''
        return f'<animateTransform attributeName="transform" type="scale" values="{v}" {self._common(begin)}{add}/>'

    def attr(self, name, vals, begin=None):
        return f'<animate attributeName="{name}" values="{";".join(num(x) for x in vals)}" {self._common(begin)}/>'

    def discrete(self, name, vals):
        """vals: one value per frame; compressed to change points."""
        n = len(vals)
        kt, vv = [], []
        for i, v in enumerate(vals):
            if i == 0 or v != vals[i - 1]:
                kt.append(i / n)
                vv.append(v)
        if len(vv) == 1:
            return ''
        return (f'<animate attributeName="{name}" values="{";".join(str(x) for x in vv)}" '
                f'keyTimes="{";".join(num(k) if k else "0" for k in kt)}" calcMode="discrete" {self._common()}/>')


def pivot_scale(cx, cy, anim_tag, inner):
    return f'<g transform="translate({num(cx)} {num(cy)})"><g>{anim_tag}<g transform="translate({num(-cx)} {num(-cy)})">{inner}</g></g></g>'


def raccoon(mood, season, holiday, langs):
    M = dict(MO.MOODS[mood])
    L = M['loop']
    M['breathP'] = L / max(1, round(L / M['breathP']))
    MO.MOODS['_render'] = M
    n = round(L * MO.FPS)
    frames = [MO.frame('_render', i / MO.FPS, S.TAIL_ANG) for i in range(n + 1)]
    del MO.MOODS['_render']
    A = Anim(L)
    col = lambda key: [f[key] for f in frames]

    body, body_out, body_piv = S.body_part()
    head, head_out, neck = S.head_part()
    paws, paws_out = S.paws_part()
    s_head, s_body = S.season_parts(season, body)
    h_head, h_front = S.holiday_parts(holiday)

    # tail
    names = [l[0] for l in langs]
    def seg_cols(p):
        if p == 'F':
            return ['#a7adb5', '#8c939c', '#737a84']
        if p == 'D':
            return ['#43464e', '#33353c', '#25262c']
        name = names[min(p, len(names) - 1)] if names else None
        b = LANG_COLORS.get(name, '#8f959e') if name else '#8f959e'
        return [shade(b, 0.32), b, shade(b, -0.25)]
    blobs = [S.tail_blob(r) for r in S.TAIL_R]
    def chain(kind):
        out = f'<g transform="translate({S.TAIL_BASE[0]} {S.TAIL_BASE[1]})">'
        for i, (shade_cells, outline_cells) in enumerate(blobs):
            if i:
                out += f'<g transform="translate({S.TAIL_LEN} 0)">'
            vals = [f['tail'][i] for f in frames]
            if kind == 'o':
                art = pix([(x, y, S.C['out']) for (x, y) in outline_cells])
            else:
                cc = seg_cols(S.TAIL_PATTERN[i])
                art = pix([(x, y, cc[s]) for (x, y), s in shade_cells.items()])
            out += '<g>' + A.rotate(vals) + art
        out += '</g>' * len(blobs) + '</g>' * (len(blobs) - 1) + '</g>'
        return out

    def variants(kind_key, table, side_cells):
        used = sorted(set(col(kind_key)))
        out = ''
        for k in used:
            vals = [1 if f[kind_key] == k else 0 for f in frames[:-1]]
            out += f'<g opacity="{vals[0]}">{A.discrete("opacity", vals)}{pix(side_cells(k))}</g>'
        return out

    ears = ''
    for sd, key in (('L', 'ear_l'), ('R', 'ear_r')):
        cells, out, pv = S.ear_part(sd)
        ears += f'<g>{A.rotate(col(key), *pv)}{pix(items(out) + items(cells))}</g>'
    brows = ''
    for sd, sign in (('L', -1.5), ('R', 1.5)):
        cells, pv = S.brow_part(sd)
        brows += f'<g>{A.translate([(0, b) for b in col("brow")])}{A.rotate([b * sign for b in col("brow")], *pv, additive=True)}{pix(items(cells))}</g>'
    eyes = f'<g>{A.translate([(lk, 0) for lk in col("look")])}' + variants('eyes', None, lambda k: items(S.eye_part('L', k)) + items(S.eye_part('R', k))) + '</g>'
    nose_cells, nose_piv = S.nose_part()
    nose = pivot_scale(*nose_piv, A.scale([(ns, ns) for ns in col('nose_s')]), pix(items(nose_cells)))
    nose = f'<g>{A.translate([(0, d) for d in col("nose_dy")])}{nose}</g>'
    mouths = variants('mouth', None, lambda k: items(S.mouth_part(k)))
    muzzle = pivot_scale(*S.MUZ, A.scale([(1 + (m - 1) * 0.6, m) for m in col('muz')]), pix(items(S.muzzle_part())) + nose + mouths)
    blush = ''
    for sd in ('L', 'R'):
        cells, pv = S.blush_part(sd)
        blush += f'<g opacity="0.5">{A.attr("opacity", col("blush"))}' + pivot_scale(*pv, A.scale([(c, c) for c in col('cheek')]), pix(items(cells))) + '</g>'
    whisk = ''
    for sd, key in (('L', 'whisk_l'), ('R', 'whisk_r')):
        cells, pv = S.whisker_part(sd)
        whisk += f'<g>{A.rotate(col(key), *pv)}{pix(items(cells))}</g>'
    head_inner = ears + pix(items(head_out) + items(head)) + brows + eyes + muzzle + blush + whisk + pix(s_head) + pix(h_head)
    head_g = (f'<g>{A.translate([(0, f["head_dy"]) for f in frames])}<g transform="translate({neck[0]} {neck[1]})"><g>'
              f'{A.rotate(col("tilt"))}{A.scale([(f["hsx"], f["hsy"]) for f in frames], additive=True)}'
              f'<g transform="translate({-neck[0]} {-neck[1]})">{head_inner}</g></g></g></g>')
    body_g = pivot_scale(*body_piv, A.scale([(1, f['body_sy']) for f in frames]), pix(items(body_out) + items(body)) + pix(s_body))
    return (chain('o') + chain('f') + body_g + head_g + pix(items(paws_out) + items(paws)) + pix(h_front)
            + effects(mood, holiday))


def effects(mood, holiday):
    out = ''
    if mood == 'sleeping':
        Z = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (4, 1), (3, 2), (2, 3), (1, 4), (0, 5), (1, 5), (2, 5), (3, 5), (4, 5), (5, 5)]
        A = Anim(3.6)
        steps = [i / 24 for i in range(25)]
        for q in range(3):
            tr = [(76 + p * 18 + 3 * math.sin(p * 6), 20 - p * 28) for p in steps]
            sc = [(0.6 + p * 0.9, 0.6 + p * 0.9) for p in steps]
            op = [1 - p for p in steps]
            out += (f'<g>{A.translate(tr, begin=-q * 1.2)}<g opacity="0">{A.attr("opacity", op, begin=-q * 1.2)}'
                    f'<g>{A.scale(sc, begin=-q * 1.2)}{pix([(x, y, "#a9bcff") for x, y in Z])}</g></g></g>')
    if mood == 'hyped' or holiday == 'valentines':
        A = Anim(1 / 1.3)
        steps = [i / 12 for i in range(13)]
        for i, (sx, sy) in enumerate([(8, 12), (82, 8), (96, 26), (134, 14), (168, 28)]):
            b = -i * 0.37 / 1.3
            if holiday == 'valentines':
                H = [(0, 0), (1, 0), (3, 0), (4, 0), (-1, 1), (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (1, 3), (2, 3), (3, 3), (2, 4)]
                art = pix([(x, y, '#ff5c8a') for x, y in H])
                out += f'<g transform="translate({sx} {sy})"><g>{A.translate([(0, -p * 10) for p in steps], begin=b)}<g>{A.attr("opacity", [1 - p for p in steps], begin=b)}{art}</g></g></g>'
            else:
                art = pix([(d, 0, '#ffd34d') for d in range(-3, 4)] + [(0, d, '#ffd34d') for d in range(-3, 4) if d])
                out += f'<g transform="translate({sx} {sy})"><g>{A.scale([(0.3 + 0.7 * math.sin(math.pi * p),) * 2 for p in steps], begin=b)}{art}</g></g>'
    return out


PARTICLES = {
    'autumn': dict(n=5, period=9, scale=1.5, shapes=[[(2, 0, 'a'), (3, 0, 'a'), (1, 1, 'a'), (2, 1, 'b'), (3, 1, 'a'), (4, 1, 'a'), (0, 2, 'a'), (1, 2, 'a'), (2, 2, 'b'), (3, 2, 'a'), (4, 2, 'a'), (5, 2, 'a'), (1, 3, 'a'), (2, 3, 'a'), (3, 3, 'b'), (4, 3, 'c'), (2, 4, 'a'), (3, 4, 'a'), (4, 4, 'c'), (5, 5, 'b')]],
                   cols=[('#e8752a', '#9a3412', '#f2b04a'), ('#c8402a', '#7a2e12', '#e8752a'), ('#f2b04a', '#9a5a12', '#ffd27a')]),
    'summer': dict(n=4, period=10, scale=1.5, shapes=[[(2, 0, 'a'), (1, 1, 'a'), (2, 1, 'b'), (3, 1, 'a'), (0, 2, 'a'), (1, 2, 'a'), (2, 2, 'b'), (3, 2, 'a'), (4, 2, 'c'), (1, 3, 'a'), (2, 3, 'b'), (3, 3, 'a'), (2, 4, 'a'), (2, 5, 'b')]],
                   cols=[('#6bcb5a', '#2f8f3f', '#9be36d'), ('#9be36d', '#3f9f4f', '#c4f0a0')]),
    'spring': dict(n=7, period=8, scale=1.5, shapes=[[(1, 0, 'a'), (2, 0, 'a'), (0, 1, 'a'), (1, 1, 'c'), (2, 1, 'a'), (3, 1, 'a'), (1, 2, 'a'), (2, 2, 'a'), (2, 3, 'b')]],
                   cols=[('#f6a6c1', '#e07a9a', '#fff0f5'), ('#f9c6d6', '#f6a6c1', '#ffffff')]),
    'winter': dict(n=12, period=11, scale=1.2, shapes=[[(1, 0, 'a'), (0, 1, 'a'), (1, 1, 'a'), (2, 1, 'a'), (1, 2, 'a')],
                                                       [(2, 0, 'a'), (0, 2, 'a'), (2, 2, 'c'), (4, 2, 'a'), (2, 4, 'a'), (1, 1, 'b'), (3, 1, 'b'), (1, 3, 'b'), (3, 3, 'b'), (2, 1, 'a'), (1, 2, 'a'), (3, 2, 'a'), (2, 3, 'a')],
                                                       [(0, 0, 'a'), (1, 0, 'a'), (0, 1, 'a'), (1, 1, 'a')]],
                   cols=[('#ffffff', '#dfe7f0', '#ffffff')]),
}


def particles(season):
    P = PARTICLES[season]
    out = ''
    for q in range(P['n']):
        seed = math.sin(q * 91.7 + 3.1) * 10000
        rnd = seed - math.floor(seed)
        per = P['period'] * (0.8 + rnd * 0.5)
        A = Anim(per)
        x0 = 10 + ((q * 53 + rnd * 40) % (S.W - 20))
        steps = [i / 30 for i in range(31)]
        tr = [(x0 + 9 * math.sin(p * math.tau * 1.5 + q) - p * 30, -8 + p * (S.H + 6)) for p in steps]
        op = [p / 0.08 if p < 0.08 else (1 - p) / 0.12 if p > 0.88 else 1 for p in steps]
        spin_rate = 60 + rnd * 80
        rot = [(q * 40 + spin_rate * per * p) for p in steps]
        flip_rate = 2 + rnd * 2
        flip = [(math.cos(flip_rate * per * p + q), 1) for p in steps]
        shape = P['shapes'][q % len(P['shapes'])]
        cols = P['cols'][q % len(P['cols'])]
        art = pix([(x, y, cols['abc'.index(c)]) for x, y, c in shape])
        begin = -((q / P['n'] + rnd * 0.3) % 1) * per
        out += (f'<g>{A.translate(tr, begin=begin)}<g opacity="0">{A.attr("opacity", op, begin=begin)}'
                f'<g>{A.rotate(rot, begin=begin)}<g>{A.scale(flip, begin=begin)}<g transform="scale({P["scale"]})">{art}</g></g></g></g></g>')
    return out


def wrap(text, width):
    words, lines, cur = text.split(), [], ''
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) > width:
            lines.append(cur)
            cur = w
        else:
            cur = f'{cur} {w}' if cur else w
    if cur:
        lines.append(cur)
    return lines or ['']


def build(cfg):
    """cfg: name, kaomoji, holiday_line, project, tagline, mood, season, holiday, langs [(name, pct)], fact."""
    name, kao = cfg['greeting'], cfg['kaomoji']
    card_top = RACC_Y + S.GROUND * PX
    card_h = 150
    fact_lines = wrap(cfg['fact'], 92)
    fact_top = card_top + card_h + 16
    fact_h = 62 + 24 * (len(fact_lines) - 1) + 26
    H = fact_top + fact_h + 2

    chars = ''.join(
        f'<tspan fill-opacity="0">{escape(ch)}<set attributeName="fill-opacity" to="1" begin="{num(0.35 + i * 0.065)}s" fill="freeze"/></tspan>'
        for i, ch in enumerate(name))
    done = 0.35 + len(name) * 0.065
    greeting = (f'<text x="2" y="36" font-family="{SANS}" font-size="30" font-weight="700" letter-spacing="-0.6" fill="#e6edf3" xml:space="preserve">'
                f'{chars}<tspan fill="#ffb27a">▍<animate attributeName="fill-opacity" values="1;0" calcMode="discrete" dur="1s" repeatCount="indefinite"/></tspan>'
                f'<tspan font-weight="400" fill="#ffb27a" fill-opacity="0"> {escape(kao)}<set attributeName="fill-opacity" to="1" begin="{num(done + 0.15)}s" fill="freeze"/></tspan>'
                f'<tspan fill="#ffd34d" fill-opacity="0">✧<set attributeName="fill-opacity" to="1" begin="{num(done + 0.3)}s" fill="freeze"/>'
                f'<animate attributeName="fill" values="#ffd34d;#fff3b0;#ffb27a;#fff3b0" calcMode="discrete" dur="0.5s" repeatCount="indefinite"/></tspan></text>')
    hol = (f'<text x="2" y="60" font-family="{MONO}" font-size="12" letter-spacing="0.5" fill="#ffb27a">{escape(cfg["holiday_line"])}</text>'
           if cfg.get('holiday_line') else '')
    tag = cfg.get('tagline') or ''
    proj = escape(cfg['project'])
    proj_line = proj + (f'<tspan fill="#878581">, {escape(tag)}</tspan>' if tag else '')
    card = (f'<rect x="0.5" y="{card_top + 0.5}" width="{WIDTH - 1}" height="{card_h - 1}" rx="10" fill="#141414" stroke="#d4d0c9" stroke-opacity="0.15"/>'
            f'<text x="24" y="{card_top + 40}" font-family="{MONO}" font-size="10" letter-spacing="1.5" fill="#878581">CURRENTLY BUILDING</text>'
            f'<text x="24" y="{card_top + 74}" font-family="{SANS}" font-size="22" font-weight="300" letter-spacing="-0.4" fill="#d4d0c9">{proj_line}</text>')
    fact = (f'<rect x="0.5" y="{fact_top + 0.5}" width="{WIDTH - 1}" height="{fact_h - 1}" rx="10" fill="#141414" stroke="#d4d0c9" stroke-opacity="0.15"/>'
            f'<text x="24" y="{fact_top + 30}" font-family="{MONO}" font-size="10" letter-spacing="1.5" fill="#878581">FUN FACT OF THE DAY</text>'
            + ''.join(f'<text x="24" y="{fact_top + 62 + 24 * i}" font-family="{SANS}" font-size="15" font-weight="300" letter-spacing="-0.3" fill="#d4d0c9">{escape(l)}</text>'
                      for i, l in enumerate(fact_lines)))
    rac = raccoon(cfg['mood'], cfg['season'], cfg['holiday'], cfg['langs'])
    title = f"Hi, I'm {cfg['greeting'].split(' ')[-1]}" if False else name
    alt = escape(f"{name} {kao}. {cfg.get('holiday_line') or ''} Currently building {cfg['project']}. Fun fact: {cfg['fact']}")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{H}" viewBox="0 0 {WIDTH} {H}" role="img" aria-label="{alt}">'
            f'<title>{alt}</title>'
            f'{greeting}{hol}{card}'
            f'<g transform="translate({RACC_X} {RACC_Y}) scale({PX})" shape-rendering="crispEdges">{rac}{particles(cfg["season"])}</g>'
            f'{fact}</svg>')
