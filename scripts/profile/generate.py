"""Regenerates assets/profile.svg (the whole README image) from profile.json + live GitHub data.

Overrides (workflow inputs or env): PROJECT, TAGLINE, SEASON, HOLIDAY, MOOD, NEW_FACT=1, OFFLINE=1
"""
import hashlib
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import data
import motion
import render

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / 'profile.json'
OUT = ROOT / 'assets' / 'profile.svg'
README = ROOT / 'README.md'
RAW = 'https://raw.githubusercontent.com/{user}/{user}/main/assets/profile.svg'


def main():
    cfg = json.loads(CONFIG.read_text(encoding='utf-8'))
    changed = False
    for key in ('project', 'tagline', 'season', 'holiday', 'mood'):
        v = os.environ.get(key.upper(), '').strip()
        if v:
            cfg[key] = v
            changed = True

    offline = os.environ.get('OFFLINE') == '1'
    user = cfg['user']
    d = data.today()

    commits = cfg.get('_last', {}).get('commits', 0)
    langs = cfg.get('_last', {}).get('langs', [])
    if not offline:
        try:
            commits = data.commits_last_week(user)
        except Exception as e:
            print('commits failed:', e)
        try:
            langs = data.top_languages(user) or langs
        except Exception as e:
            print('languages failed:', e)
    fact = cfg.get('_last', {}).get('fact') or 'Raccoons can rotate their hind feet 180 degrees to climb down trees head first.'
    if not offline and (os.environ.get('NEW_FACT') == '1' or cfg.get('_last', {}).get('fact_date') != d.isoformat()):
        try:
            fact = data.fun_fact()
            cfg.setdefault('_last', {})['fact_date'] = d.isoformat()
        except Exception as e:
            print('fact failed:', e)

    mood = cfg.get('mood', 'auto')
    mood = motion.mood_for(commits) if mood == 'auto' else mood
    season = cfg.get('season', 'auto')
    season = data.season_for(d) if season == 'auto' else season
    holiday = cfg.get('holiday', 'auto')
    holiday = data.holiday_for(d, cfg.get('birthday')) if holiday == 'auto' else holiday

    svg = render.build(dict(greeting=cfg['greeting'], kaomoji=cfg['kaomoji'], holiday_line=data.HOLIDAY_LINES.get(holiday, ''),
                            project=cfg['project'], tagline=cfg.get('tagline', ''), mood=mood, season=season,
                            holiday=holiday, langs=langs or [('TypeScript', 100)], fact=fact))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding='utf-8')
    version = hashlib.sha256(svg.encode('utf-8')).hexdigest()[:12]
    alt = f"{cfg['greeting']} {cfg['kaomoji']}✧ Currently building {cfg['project']}."
    img = f'<img src="{RAW.format(user=user)}?v={version}" width="820" alt="{alt}" />'
    readme = README.read_text(encoding='utf-8') if README.exists() else ''
    if '<!-- profile:start -->' in readme:
        readme = re.sub(r'<!-- profile:start -->.*?<!-- profile:end -->', f'<!-- profile:start -->\n{img}\n<!-- profile:end -->', readme, flags=re.S)
    else:
        readme = f'<!-- profile:start -->\n{img}\n<!-- profile:end -->\n'
    README.write_text(readme, encoding='utf-8')
    cfg['_last'] = dict(cfg.get('_last', {}), commits=commits, langs=langs, fact=fact, mood=mood, season=season,
                        holiday=holiday, date=d.isoformat())
    CONFIG.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'{d} commits={commits} mood={mood} season={season} holiday={holiday} langs={langs} '
          f'size={len(svg) // 1024}KB{" (config changed)" if changed else ""}')


if __name__ == '__main__':
    main()
