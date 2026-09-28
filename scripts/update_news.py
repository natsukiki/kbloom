"""
Soompi RSS から最新K-POPニュースを取得し、index.html の NEWS データを更新する。
毎日 GitHub Actions で自動実行される。
"""
import feedparser
import json
import re
import html
from datetime import datetime

RSS_URL = "https://soompi.com/category/news/feed/"
KPOP_GROUPS = [
    "BLACKPINK","aespa","NewJeans","IVE","LE SSERAFIM","TWICE","ILLIT",
    "BABYMONSTER","(G)I-DLE","ITZY","STRAY KIDS","BTS","EXO","NCT",
    "SEVENTEEN","ATEEZ","TXT","ENHYPEN","JENNIE","LISA","KARINA","WINTER"
]
PALETTES = [
    ["#FFD880","#FF9860"],["#FFD4A0","#FFB0CC"],["#D8C8FF","#C0E4FF"],
    ["#A8D8FF","#B8F8E0"],["#FFA8A8","#A8A8FF"],["#FFB8D0","#FFD8A0"],
    ["#C8C0FF","#A8E8C0"],["#A8D8FF","#C8F8E8"]
]

def strip_html(s):
    s = re.sub(r'<[^>]+>', '', s or '')
    return html.unescape(s).strip()

def find_group(title):
    for g in KPOP_GROUPS:
        if g in title:
            return g
    return ""

def cat_from_title(title):
    tl = title.lower()
    if any(k in tl for k in ['concert','tour','perform']):
        return 'コンサート'
    if any(k in tl for k in ['album','release','comeback','single','mv']):
        return 'リリース'
    if any(k in tl for k in ['chart','record','million','award','win']):
        return '記録'
    if any(k in tl for k in ['fashion','brand','ambassador','wear','outfit']):
        return 'ファッション'
    return 'ニュース'

def fetch_news():
    feed = feedparser.parse(RSS_URL)
    items = []
    for i, entry in enumerate(feed.entries[:8]):
        title = entry.get('title', '')
        desc = strip_html(entry.get('summary', entry.get('description', '')))
        grp = find_group(title)
        pub = entry.get('published', '')[:10].replace('-', '.')
        items.append({
            'id': f'ln{i}',
            'emoji': '📰',
            'cat': cat_from_title(title),
            'group': grp,
            'headline': title,
            'date': pub,
            'desc': desc[:160] + ('…' if len(desc) > 160 else ''),
            'tags': [grp, 'Soompi'] if grp else ['K-POP', 'Soompi'],
            'colors': PALETTES[i % len(PALETTES)]
        })
    return items

def js_value(v):
    if isinstance(v, str):
        escaped = v.replace('\\', '\\\\').replace("'", "\\'")
        return f"'{escaped}'"
    if isinstance(v, list):
        return '[' + ','.join(js_value(x) for x in v) + ']'
    return str(v)

def items_to_js(items):
    rows = []
    for item in items:
        fields = ','.join(f"{k}:{js_value(v)}" for k, v in item.items())
        rows.append('{' + fields + '}')
    return 'const NEWS=[\n  ' + ',\n  '.join(rows) + '\n];'

def main():
    items = fetch_news()
    if len(items) < 2:
        print("Not enough news items fetched, skipping update.")
        return

    new_block = items_to_js(items)

    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    updated = re.sub(
        r'const NEWS=\[[\s\S]*?\];',
        new_block,
        content,
        count=1
    )

    if updated == content:
        print("NEWS block not found or unchanged.")
        return

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(updated)

    print(f"Updated {len(items)} news items on {datetime.now().strftime('%Y-%m-%d')}")

if __name__ == '__main__':
    main()
