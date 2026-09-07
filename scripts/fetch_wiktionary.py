# -*- coding: utf-8 -*-
"""위키낱말사전 '분류:한국어 한자성어' 에서 네 글자 성어의 뜻·한자·예문을 뽑는다.

한국어기초사전에는 사자성어가 178개뿐이라 각주구검·결초보은 같은 대표적인 것들이
빠져 있다. 이를 보충한다. 위키낱말사전은 CC BY-SA 4.0 이다.

결과: data/wiktionary_sajaseongeo.json
"""
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://ko.wiktionary.org/w/api.php"
UA = "daily-ko-bot/1.0 (https://github.com/jeochris/fluent-korean)"
CATEGORY = "분류:한국어 한자성어"


def api(params):
    params.update({"action": "query", "format": "json"})
    url = API + "?" + urllib.parse.urlencode(params)
    for _ in range(6):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            return json.load(urllib.request.urlopen(req, timeout=30))
        except urllib.error.HTTPError as e:
            if e.code == 429:  # 레이트 리밋. 잠깐 쉬고 다시.
                time.sleep(8)
                continue
            raise
    raise RuntimeError("API 재시도 초과")


def members():
    out, cont = [], None
    while True:
        p = {"list": "categorymembers", "cmtitle": CATEGORY, "cmlimit": "500"}
        if cont:
            p["cmcontinue"] = cont
        r = api(p)
        out += [m["title"] for m in r["query"]["categorymembers"]]
        cont = r.get("continue", {}).get("cmcontinue")
        if not cont:
            return out
        time.sleep(1)


def sources(titles):
    out = {}
    for i in range(0, len(titles), 50):
        r = api({"prop": "revisions", "rvprop": "content", "rvslots": "main",
                 "titles": "|".join(titles[i:i + 50])})
        for pg in r["query"]["pages"].values():
            if "revisions" in pg:
                out[pg["title"]] = pg["revisions"][0]["slots"]["main"]["*"]
        time.sleep(1)
    return out


def clean(t):
    t = re.sub(r"\{\{따옴\|(.*?)\}\}", "", t)
    t = re.sub(r"\{\{[^{}]*\}\}", "", t)
    t = re.sub(r"\[\[([^\]|]*\|)?([^\]]*)\]\]", r"\2", t)
    t = t.replace("'''", "").replace("''", "")
    t = re.sub(r"^\s*\((?:사자성어|한자성어|고사성어)\)\s*", "", t)
    return re.sub(r"\s+", " ", t).strip()


def parse(word, src):
    ko = src.split("== 한국어 ==")[-1]

    hanja = None
    for pat in (r"어원:.*?한자 \[\[([^\]|]+)\]\]",
                r"\(한자 \[\[([^\]|]+)\]\]\)",
                r"\{\{어원\|([一-鿿]{2,8})\|"):
        m = re.search(pat, ko)
        if m:
            hanja = m.group(1)
            break

    means = [clean(l[2:]) for l in ko.split("\n") if l.startswith("# ")]
    means = [m for m in means if len(m) >= 8]
    if not means:
        return None

    example = None
    for l in ko.split("\n"):
        if l.startswith(":*"):
            e = clean(l[2:])
            if len(e) >= 10 and word in e:
                example = e
                break

    item = {"word": word, "mean": means[0], "source": "wiktionary"}
    if hanja:
        item["hanja"] = hanja
    if example:
        item["example"] = example
    return item


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    titles = [m for m in members() if re.match(r"^[가-힣]{4}$", m)]
    print(f"{CATEGORY}: 4음절 {len(titles)}개")

    out = []
    for word, src in sources(titles).items():
        it = parse(word, src)
        if it:
            out.append(it)
    out.sort(key=lambda x: x["word"])

    path = os.path.join(root, "data", "wiktionary_sajaseongeo.json")
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"  뜻 추출 {len(out)}개 / 한자 {sum(1 for x in out if x.get('hanja'))}개 "
          f"/ 예문 {sum(1 for x in out if x.get('example'))}개")


if __name__ == "__main__":
    main()
