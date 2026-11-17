"""Live inputs: commit count, languages, season, upcoming holiday, fun fact."""
import datetime as dt
import json
import os
import urllib.request

API = 'https://api.github.com'
LUNAR_NEW_YEAR = {2026: (2, 17), 2027: (2, 6), 2028: (1, 26), 2029: (2, 13), 2030: (2, 3), 2031: (1, 23), 2032: (2, 11)}


def _get(url, data=None):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'profile-raccoon'}
    token = os.environ.get('GITHUB_TOKEN')
    if token and url.startswith(API):
        headers['Authorization'] = f'Bearer {token}'
    if data is not None:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(data).encode()
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def today(tz_hours=-8):
    return (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=tz_hours)).date()


def commits_last_week(user, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    start = now - dt.timedelta(days=7)
    if os.environ.get('GITHUB_TOKEN'):
        try:
            q = ('query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){contributionsCollection(from:$from,to:$to)'
                 '{totalCommitContributions restrictedContributionsCount}}}')
            r = _get(f'{API}/graphql', {'query': q, 'variables': {'login': user, 'from': start.isoformat(), 'to': now.isoformat()}})
            c = r['data']['user']['contributionsCollection']
            return int(c['totalCommitContributions']) + int(c.get('restrictedContributionsCount') or 0)
        except Exception as e:
            print('graphql commits failed, using events:', e)
    total = 0
    for ev in _get(f'{API}/users/{user}/events/public?per_page=100'):
        when = dt.datetime.fromisoformat(ev['created_at'].replace('Z', '+00:00'))
        if when >= start and ev['type'] == 'PushEvent':
            total += max(1, int(ev['payload'].get('distinct_size') or ev['payload'].get('size') or 1))
    return total


def top_languages(user, days=60, limit=4, skip=('profile',)):
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    repos = _get(f'{API}/users/{user}/repos?type=owner&sort=pushed&per_page=100')
    totals = {}
    for repo in repos:
        if repo.get('fork') or repo['name'] == user:
            continue
        pushed = dt.datetime.fromisoformat(repo['pushed_at'].replace('Z', '+00:00'))
        if pushed < cutoff:
            continue
        for lang, n in _get(repo['languages_url']).items():
            totals[lang] = totals.get(lang, 0) + n
    if not totals:
        return []
    s = sum(totals.values())
    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:limit]
    return [(name, round(100 * n / s)) for name, n in ranked]


def season_for(d):
    m = d.month
    return 'spring' if m in (3, 4, 5) else 'summer' if m in (6, 7, 8) else 'autumn' if m in (9, 10, 11) else 'winter'


def _thanksgiving(year):
    d = dt.date(year, 11, 1)
    first_thu = d + dt.timedelta(days=(3 - d.weekday()) % 7)
    return first_thu + dt.timedelta(weeks=3)


def holiday_for(d, birthday=None, lead=13):
    """Name of the holiday d falls in the run-up to (lead days before through the day), or 'none'."""
    cands = []
    for y in (d.year, d.year + 1):
        cands += [('halloween', dt.date(y, 10, 31)), ('thanksgiving', _thanksgiving(y)), ('christmas', dt.date(y, 12, 25)),
                  ('valentines', dt.date(y, 2, 14))]
        if y in LUNAR_NEW_YEAR:
            cands.append(('lunarnewyear', dt.date(y, *LUNAR_NEW_YEAR[y])))
        if birthday:
            m, day = (int(x) for x in birthday.split('-'))
            cands.append(('birthday', dt.date(y, m, day)))
    best = None
    for name, day in cands:
        if 0 <= (day - d).days <= lead and (best is None or day < best[1]):
            best = (name, day)
    if best is None and (d.month == 12 and d.day >= 26 or d.month == 1 and d.day <= 2):
        return 'newyear'
    return best[0] if best else 'none'


HOLIDAY_LINES = {'halloween': 'happy halloween', 'thanksgiving': 'happy thanksgiving', 'christmas': 'merry christmas',
                 'newyear': 'happy new year', 'lunarnewyear': 'happy lunar new year', 'valentines': "happy valentine's day",
                 'birthday': 'birthday week', 'none': ''}


def fun_fact():
    r = _get('https://uselessfacts.jsph.pl/api/v2/facts/random?language=en')
    return r['text'].strip()
