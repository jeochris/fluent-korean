import json, glob, collections

def feats(o):
    f = o.get('feat')
    if f is None: return {}
    if isinstance(f, dict): f = [f]
    return {x['att']: x['val'] for x in f if isinstance(x, dict) and 'att' in x and 'val' in x}

def examples(sense):
    ex = sense.get('SenseExample', [])
    if isinstance(ex, dict): ex = [ex]
    out = []
    for e in ex:
        fe = feats(e)
        if fe.get('type') == '문장' and fe.get('example'):
            out.append(fe['example'])
    return out

buckets = collections.defaultdict(list)
stats = collections.Counter()

for path in sorted(glob.glob('krdict/*.json')):
    entries = json.load(open(path))['LexicalResource']['Lexicon']['LexicalEntry']
    for e in entries:
        fe = feats(e)
        unit = fe.get('lexicalUnit')
        level = fe.get('vocabularyLevel')
        lem = e['Lemma']
        if isinstance(lem, list): lem = lem[0]
        word = feats(lem).get('writtenForm')
        if not word: continue
        senses = e.get('Sense', [])
        if isinstance(senses, dict): senses = [senses]
        for s in senses:
            fs = feats(s)
            d = fs.get('definition')
            if not d: continue
            item = {'word': word, 'mean': d}
            if fe.get('origin'): item['hanja'] = fe['origin']
            if fe.get('partOfSpeech') and fe['partOfSpeech'] != '품사 없음':
                item['pos'] = fe['partOfSpeech']
            if fe.get('semanticCategory'): item['category'] = fe['semanticCategory']
            ex = examples(s)
            if ex: item['example'] = ex[0]
            if unit == '속담':
                buckets['proverb'].append(item)
            elif unit == '관용구':
                buckets['idiom_phrase'].append(item)
            elif unit == '단어' and level in ('고급', '중급'):
                item['level'] = level
                buckets['word_' + level].append(item)
        stats[unit] += 1
        stats['level:' + str(level)] += 1
    print('done', path, flush=True)

for k, v in buckets.items():
    seen, uniq = set(), []
    for it in v:
        key = (it['word'], it['mean'])
        if key in seen: continue
        seen.add(key); uniq.append(it)
    json.dump(uniq, open(f'out_{k}.json', 'w'), ensure_ascii=False, indent=1)
    print(f'{k}: {len(v)} -> {len(uniq)} unique')
print(stats.most_common(20))
