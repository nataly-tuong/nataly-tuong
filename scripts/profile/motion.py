"""Raccoon motion: the same timelines as the design, sampled per frame."""
import math

TAU = math.tau
FPS = 24

EXPR = {
    'neutral': dict(eyes='open', mouth='smile', brow=0, cheek=1, muz=1, ear=0, sq=0, blush=0.5),
    'smile': dict(eyes='happy', mouth='w', brow=-1.3, cheek=1.3, muz=1.03, ear=6, sq=0.3, blush=0.75),
    'laugh': dict(eyes='happy', mouth='grin', brow=-2.2, cheek=1.45, muz=1.08, ear=9, sq=1, blush=0.9),
    'curious': dict(eyes='big', mouth='o', brow=-2.8, cheek=0.95, muz=0.97, ear=11, sq=-0.6, blush=0.45),
    'sleepy': dict(eyes='half', mouth='smile', brow=1.3, cheek=0.9, muz=1, ear=-14, sq=0, blush=0.4),
    'yawn': dict(eyes='closed', mouth='yawn', brow=1.9, cheek=0.85, muz=1.16, ear=-6, sq=-1.2, blush=0.4),
    'asleep': dict(eyes='closed', mouth='sleep', brow=1, cheek=1, muz=1, ear=-10, sq=0, blush=0.55),
    'snore': dict(eyes='closed', mouth='o', brow=1, cheek=1.08, muz=1.05, ear=-10, sq=0.2, blush=0.6),
}

MOODS = {
    'sleeping': dict(loop=12, breathP=4, breathA=0.04, tailW=0.55, tailZ=0.28, tailEvents=[(8.2, 6, 'tip')],
                     tilt=[(0, 0), (6, -2), (11, 0)], earL=[5.1], earR=[],
                     expr=[(0, 'asleep'), (3.6, 'snore'), (4.3, 'asleep'), (9.6, 'snore'), (10.3, 'asleep')],
                     nose=[6.6], blinks=[], glance=[]),
    'lazy': dict(loop=10, breathP=3.4, breathA=0.028, tailW=0.9, tailZ=0.22, tailEvents=[(1.4, 10, None), (4.2, -8, None)],
                 tilt=[(0, 0), (2.2, 3), (4.8, 0), (5.5, 2), (5.8, -11), (7.8, -11), (8.0, 4), (8.3, -2), (8.6, 0)],
                 earL=[3.3], earR=[9.0],
                 expr=[(0, 'sleepy'), (5.75, 'yawn'), (7.85, 'sleepy'), (8.6, 'smile'), (9.5, 'sleepy')],
                 nose=[3.0], blinks=[], glance=[]),
    'happy': dict(loop=8, breathP=3.0, breathA=0.024, tailW=1.25, tailZ=0.2,
                  tailEvents=[(0.5, 16, None), (3.0, -13, None), (5.6, 20, None), (6.5, -10, None)],
                  tilt=[(0, 0), (1.3, 7), (2.9, 0), (3.9, -9), (4.9, 0), (5.7, 2), (6.9, 5), (7.4, 0)],
                  earL=[2.1, 7.6], earR=[4.4],
                  expr=[(0, 'neutral'), (1.3, 'smile'), (2.9, 'neutral'), (3.9, 'curious'), (4.9, 'neutral'), (5.7, 'laugh'), (6.9, 'smile'), (7.4, 'neutral')],
                  nose=[2.4, 4.4], shake=(5.75, 6.75), blinks=[(0.9, 0.1), (3.4, 0.1), (7.7, 0.1)],
                  glance=[(0, 0), (4.15, 1), (4.55, -1), (4.9, 0)]),
    'hyped': dict(loop=4.8, breathP=0.6, breathA=0.05, tailW=2.2, tailZ=0.18,
                  tailEvents=[(0, 18, None), (0.6, -18, None), (1.2, 18, None), (1.8, -18, None), (2.4, 18, None), (3.0, -18, None), (3.6, 18, None), (4.2, -18, None)],
                  tilt=[(0, 0), (0.6, 8), (1.2, -8), (1.8, 8), (2.4, -8), (3.0, 8), (3.6, -8), (4.2, 0)],
                  earL=[0.3, 1.5, 2.7, 3.9], earR=[0.9, 2.1, 3.3, 4.5],
                  expr=[(0, 'laugh'), (1.2, 'smile'), (1.8, 'laugh'), (3.0, 'smile'), (3.6, 'laugh')],
                  nose=[0.9, 3.3], blinks=[], glance=[], hop=0.6),
}


def mood_for(commits):
    return 'sleeping' if commits <= 0 else 'lazy' if commits <= 5 else 'happy' if commits <= 20 else 'hyped'


def ease_out_back(x):
    c1 = 1.9
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def key_at(keys, t):
    i = 0
    for k, (t0, _) in enumerate(keys):
        if t0 <= t:
            i = k
    return i


def track(keys, t, dur):
    i = key_at(keys, t)
    prev, cur = keys[i - 1][1], keys[i][1]
    u = (t - keys[i][0]) / dur
    return cur if u >= 1 else prev + (cur - prev) * ease_out_back(max(0.0, u))


def flick(t, times, loop, amp):
    a = 0.0
    for t0 in times:
        u = (t - t0 + loop) % loop
        if u < 0.07:
            a += -0.25 * amp * (u / 0.07)
        elif u < 1.2:
            a += amp * math.exp(-6 * (u - 0.07)) * math.cos(15 * (u - 0.07))
    return a


def frame(mood, t, tail_base_angles):
    """All animated values for one frame (t in seconds, within the mood loop)."""
    M = MOODS[mood]
    L = M['loop']
    n = len(tail_base_angles)
    w = TAU / M['tailW'] * 0.9
    tail = []
    for i in range(n):
        wave = 0.0
        for (t0, A, where) in M['tailEvents']:
            if where == 'tip' and i < n - 6:
                continue
            tau = ((t - t0 - i * 0.05) % L + L) % L
            gain = (i - (n - 6)) / 6 if where == 'tip' else 0.35 + i * 0.09
            wave += A * gain * math.exp(-M['tailZ'] * w * tau) * math.sin(w * tau) / (1 + i * 0.02)
        tail.append(tail_base_angles[i] + wave * 0.6)

    keys = M['expr']
    ei = key_at(keys, t)
    cur, prev = EXPR[keys[ei][1]], EXPR[keys[ei - 1][1]]
    eu = min(1.0, (t - keys[ei][0]) / 0.16)
    k = ease_out_back(eu)
    mix = lambda key: prev[key] + (cur[key] - prev[key]) * k
    brow, cheek, muz, ear_base, sq, blush = (mix(x) for x in ('brow', 'cheek', 'muz', 'ear', 'sq', 'blush'))
    eyes, mouth = cur['eyes'], cur['mouth']
    if eu < 0.35 and prev['eyes'] != cur['eyes'] and cur['eyes'] != 'closed':
        eyes = 'closed'
    if eyes in ('open', 'big'):
        for (b0, d) in M['blinks']:
            if b0 <= t < b0 + d:
                eyes = 'closed'

    breath = math.sin(TAU * t / M['breathP'])
    scale_y = 1 + M['breathA'] * breath
    head_dy = -M['breathA'] * 16 * breath
    tilt = track(M['tilt'], t, 0.2)
    if 'shake' in M and M['shake'][0] < t < M['shake'][1]:
        s0, s1 = M['shake']
        tilt += 3.5 * math.sin(TAU * 5 * (t - s0)) * (1 - (t - s0) / (s1 - s0))
    hsx, hsy = 1 + 0.035 * sq, 1 - 0.045 * sq
    if 'hop' in M:
        c = (t % M['hop']) / M['hop']
        air = 0 if c < 0.18 else math.sin(math.pi * (c - 0.18) / 0.82)
        head_dy = -4.5 * air
        scale_y = 0.93 + 0.07 * (c / 0.18) if c < 0.18 else 1 + 0.035 * air
        if c < 0.18:
            hsx *= 1.05; hsy *= 0.94
        else:
            hsx *= 1 - 0.02 * air; hsy *= 1 + 0.03 * air
    look = round(track(M['glance'], t, 0.06)) if M['glance'] else 0
    eb = ear_base * 0.5 if ear_base >= 0 else ear_base
    ear_l = eb + flick(t, M['earL'], L, -20)
    ear_r = -eb + flick(t, M['earR'], L, 20)
    nose_dy, nose_s = 0.0, 1.0
    for n0 in M['nose']:
        u = (t - n0 + L) % L
        if u < 0.36:
            ph = int(u / 0.06) % 2
            nose_dy, nose_s = (-0.7, 1.15) if ph else (0.2, 0.95)
    wl = flick(t, [1.1, 4.4], L, 6) + (cheek - 1) * -12
    wr = flick(t, [1.25, 4.55], L, -6) + (cheek - 1) * 12
    return dict(tail=tail, body_sy=scale_y, head_dy=head_dy, tilt=tilt, hsx=hsx, hsy=hsy, ear_l=ear_l, ear_r=ear_r,
                brow=brow, eyes=eyes, look=look, muz=muz, nose_dy=nose_dy, nose_s=nose_s, mouth=mouth,
                cheek=cheek, blush=blush, whisk_l=wl, whisk_r=wr)
