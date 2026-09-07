# -*- coding: utf-8 -*-
"""위키백과 본문에 각 사자성어가 몇 번 등장하는지 센다. 통용도(= 쉬움) 판정에 쓴다.

너무 흔한 사자성어를 빼기 위한 자료다. 속담·관용구는 위키백과가 백과사전
문체라서 쉬운 것도 1~5회밖에 안 나와 이 방법이 통하지 않는다. 사자성어만 쓴다.

중간 저장을 하므로 끊겨도 다시 실행하면 이어서 받는다.
결과: data/wiki_freq.json  {"이심전심": 27, ...}
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://ko.wikipedia.org/w/api.php"
UA = "daily-ko-bot/1.0 (https://github.com/jeochris/fluent-korean)"
DELAY = 1.2       # 0.35초로 돌렸다가 429 에 계속 걸렸다. 이 정도는 되어야 안정적이다.
SAVE_EVERY = 20


def hits(word):
    p = {"action": "query", "format": "json", "list": "search",
         "srsearch": f'"{word}"', "srlimit": "1", "srinfo": "totalhits", "srwhat": "text"}
    url = API + "?" + urllib.parse.urlencode(p)
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            r = json.load(urllib.request.urlopen(req, timeout=30))
            return r["query"]["searchinfo"]["totalhits"]
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(5 * (attempt + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            time.sleep(3)
    return None


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_path = os.path.join(root, "data", "wiki_freq.json")
    data = json.load(open(os.path.join(root, "data", "daily_ko.json"), encoding="utf-8"))
    words = [x["word"] for x in data["sajaseongeo"]]

    res = {}
    if os.path.exists(out_path):
        res = json.load(open(out_path, encoding="utf-8"))
    todo = [w for w in words if w not in res]
    print(f"전체 {len(words)} / 이미 받음 {len(res)} / 남음 {len(todo)}", flush=True)

    for i, w in enumerate(todo, 1):
        res[w] = hits(w)
        if i % SAVE_EVERY == 0 or i == len(todo):
            json.dump(res, open(out_path, "w", encoding="utf-8"), ensure_ascii=False)
            done = len(res)
            print(f"  {done}/{len(words)}  ({done / len(words) * 100:.0f}%)  마지막: {w}={res[w]}",
                  flush=True)
        time.sleep(DELAY)

    print(f"완료: {len(res)}개", flush=True)


if __name__ == "__main__":
    main()
