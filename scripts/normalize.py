# -*- coding: utf-8 -*-
"""데이터 정리.

1. 위키낱말사전에서 뽑은 사자성어를 합친다 (한국어기초사전에 178개뿐이라 보충).
2. 사자성어는 네 글자만 남긴다.
3. 같은 표제어의 여러 뜻은 한 항목으로 합친다. 한국어기초사전은 다의어를 뜻마다
   별도 항목으로 담고 있어, 그대로 두면 봇이 같은 말을 며칠 간격으로 다시 올리는
   것처럼 보인다.
"""
import json
import os
import re
import sys

MAX_SENSES = 3  # 슬랙 메시지가 길어지지 않게 뜻은 최대 3개까지만


def merge(group):
    means, out = [], dict(group[0])
    for g in group:
        m = g['mean'].strip()
        if m not in means:
            means.append(m)
    if len(means) > 1:
        kept = means[:MAX_SENSES]
        out['mean'] = ' '.join(f'{i}. {m}' for i, m in enumerate(kept, 1))
    else:
        out['mean'] = means[0]
    for g in group:  # 예문·한자는 가진 항목에서 가져온다
        if g.get('example') and not out.get('example'):
            out['example'] = g['example']
        if g.get('hanja') and not out.get('hanja'):
            out['hanja'] = g['hanja']
    return out


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, 'data', 'daily_ko.json')
    data = json.load(open(path, encoding='utf-8'))

    # 출처가 섞이므로 표기를 위해 기존 항목에 출처를 명시한다
    for key in ('sajaseongeo', 'sokdam', 'gwanyonggu'):
        for x in data[key]:
            x.setdefault('source', 'krdict')

    # 위키낱말사전 보충분 병합 (같은 표제어는 한국어기초사전 쪽을 우선한다)
    extra_path = os.path.join(root, 'data', 'wiktionary_sajaseongeo.json')
    if os.path.exists(extra_path):
        have = {x['word'].strip() for x in data['sajaseongeo']}
        extra = [x for x in json.load(open(extra_path, encoding='utf-8'))
                 if x['word'].strip() not in have]
        print(f'위키낱말사전 병합: +{len(extra)}')
        data['sajaseongeo'] += extra

    # 사자성어는 네 글자만
    before = len(data['sajaseongeo'])
    data['sajaseongeo'] = [x for x in data['sajaseongeo']
                           if re.match(r'^[가-힣]{4}$', x['word'].strip())]
    print(f'사자성어 4음절 필터: {before} → {len(data["sajaseongeo"])}')

    for key in ('sajaseongeo', 'sokdam', 'gwanyonggu'):
        groups = {}
        for x in data[key]:
            groups.setdefault(x['word'].strip(), []).append(x)
        merged = []
        for word, g in groups.items():
            it = merge(g)
            it['word'] = word
            merged.append(it)
        print(f'  {key:12} {len(data[key]):>5} → {len(merged):>5} (표제어 기준 병합)')
        data[key] = merged

    json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
