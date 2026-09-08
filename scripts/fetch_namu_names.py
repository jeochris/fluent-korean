# -*- coding: utf-8 -*-
"""나무위키 '분류:사자성어' 에서 성어 이름만 모은다.

이름 목록은 사실 데이터라 그대로 쓰고, 뜻풀이는 국립국어원·위키낱말사전 등
CC BY-SA 출처에서 가져온다. 나무위키 본문(CC BY-NC-SA)은 한 줄도 쓰지 않는다.

결과: data/namu_names.json  (네 글자 성어 이름 목록)
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

BASE = "https://namu.wiki/w/" + urllib.parse.quote("분류:사자성어")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"
DELAY = 1.5


def fetch(cfrom=None):
    url = BASE + "?namespace=" + urllib.parse.quote("문서")
    if cfrom:
        url += "&cfrom=" + urllib.parse.quote(cfrom)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def parse(html):
    """(이 페이지의 4음절 성어들, 다음 페이지 cfrom) 을 돌려준다."""
    words = sorted({urllib.parse.unquote(x)
                    for x in re.findall(r'/w/([^"\'<>\\?]+)', html)
                    if re.match(r'^[%A-Za-z0-9]+$', x)}
                   | {urllib.parse.unquote(x)
                      for x in re.findall(r'/w/([^"\'<>\\?]+)', html)})
    words = [w for w in words if re.match(r'^[가-힣]{4}$', w)]
    nxt = re.search(r'cfrom=([^"\'<>\\&]+)', html)
    return words, urllib.parse.unquote(nxt.group(1)) if nxt else None


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_path = os.path.join(root, "data", "namu_names.json")

    seen, cfrom, page = set(), None, 0
    while True:
        html = fetch(cfrom)
        words, nxt = parse(html)
        new = [w for w in words if w not in seen]
        seen.update(words)
        page += 1
        print(f"  {page}쪽  +{len(new):>3}  누적 {len(seen):>4}  다음={nxt}", flush=True)
        if not nxt or not new:
            break
        cfrom = nxt
        time.sleep(DELAY)

    json.dump(sorted(seen), open(out_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"완료: {len(seen)}개 → {out_path}")


if __name__ == "__main__":
    main()
