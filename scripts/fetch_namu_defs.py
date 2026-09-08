# -*- coding: utf-8 -*-
"""나무위키 '분류:사자성어' 문서에서 뜻풀이를 가져온다.

국립국어원·위키낱말사전 어디에도 없는 성어를 채우기 위한 것이다.
나무위키는 CC BY-NC-SA 2.0 KR 이라 CC BY-SA 인 나머지 데이터와 라이선스가
다르다. 그래서 별도 파일로 두고 항목마다 출처를 남긴다.

결과: data/namu_sajaseongeo.json
"""
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "Chrome/120 Safari/537.36")
DELAY = 1.5
HANJA = r'㐀-䶿一-鿿豈-﫿'


def fetch(word):
    url = "https://namu.wiki/w/" + urllib.parse.quote(word)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for _ in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                time.sleep(6)
                continue
            return None
        except (urllib.error.URLError, TimeoutError):
            time.sleep(3)
    return None


def plain(h):
    b = re.sub(r'<script.*?</script>', ' ', h, flags=re.S)
    b = re.sub(r'<style.*?</style>', ' ', b, flags=re.S)
    t = html.unescape(re.sub(r'<[^>]+>', ' ', b))
    return re.sub(r'\s+', ' ', t)


# 개요 절 뒤에 문서 푸터와 광고가 붙어 들어온다. 처음 나오는 경계에서 자른다.
BOUNDARY = re.compile(
    r'\S*\.(?:kr|com|net)\b'
    r'|이 저작물은|나무위키|CC BY|리그 오브 레전드'
    r'|관련 문서|같이 보기|둘러보기|분류\s*:'
    r'|실시간 견적|무료 ?상담|대출|보험료|보험 ?비교|견적받기|최저가|쇼핑')


def tidy(s):
    s = re.sub(r'\[편집\]|\[\d+\]', ' ', s)
    m = BOUNDARY.search(s)
    if m:
        s = s[:m.start()]
    # 한자 낱글자 사이에 들어간 공백을 붙인다: "권( 勸 )함" -> "권(勸)함"
    s = re.sub(rf'\(\s*([{HANJA}\s]+?)\s*\)', lambda m: '(' + re.sub(r'\s+', '', m.group(1)) + ')', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def strip_lead(word, mean):
    """뜻 앞에 붙은 한자·훈음 덩어리를 떼어낸다.

    "고사성어 太 平 歲 月 통할 태 평평할 평 세월 세 세월 월 근심이나 걱정이 없는 시절."
    처럼 개요 절이 시작되는 문서가 있다. 훈음은 낱글자 수가 일정하지 않아
    (예: "큰 기러기 홍") 개수로는 못 자른다. 대신 표제어의 마지막 음절이
    훈음의 끝이라는 점을 쓴다.
    """
    m = re.match(rf'^(?:고사성어|사자성어|한자성어)?\s*((?:[{HANJA}]\s*){{3,8}})(.*)$', mean, re.S)
    if not m:
        return mean
    rest = m.group(2).lstrip()
    # "(유치찬란)" 처럼 독음을 괄호로 적어 둔 형태
    r2 = re.match(rf'^\(\s*{re.escape(word)}\s*\)\s*(.*)$', rest, re.S)
    if r2:
        return r2.group(1).strip()
    # 훈음 블록: 표제어 마지막 음절이 낱말로 나오는 지점까지
    tail = re.match(rf'^((?:[가-힣]+\s+){{0,16}}?{re.escape(word[-1])})\s+(.+)$', rest, re.S)
    if tail:
        return tail.group(2).strip()
    return rest


def parse(word, h):
    t = plain(h)
    # 분류가 여러 개면 "분류 동음이의어 사자성어" 처럼 사이에 다른 말이 낀다.
    if not re.search(r'분류\s.{0,60}?(?:사자|고사)성어', t):
        return None

    # 표제어 한자는 훈음(예: "많을 다 재주 재")을 뒤에 달고 나온다. 그걸 표지로 찾는다.
    hanja = None
    m = re.search(rf'([{HANJA}])\s+([{HANJA}])\s+([{HANJA}])\s+([{HANJA}])\s+'
                  rf'[가-힣]{{1,4}}\s+[가-힣]{{1,3}}\s+[가-힣]{{1,4}}\s', t)
    if m:
        hanja = ''.join(m.groups())

    # 절 제목이 문서마다 다르다: 개요 / 뜻 / 의미. 번호도 "1." 또는 "1.1." 이다.
    body = re.search(
        r'\d+(?:\.\d+)*\s*\.\s*(?:개요|뜻|의미|정의)\s*\[편집\]'
        r'(.*?)'
        r'(?=\d+(?:\.\d+)*\s*\.\s*[^\[]{1,24}\[편집\]|$)', t, re.S)
    if not body:
        return None
    mean = tidy(body.group(1))
    # 표제어의 한자를 다시 적어 두는 문서가 있다: "甲男乙女. 이름이 갑이란..."
    mean = re.sub(rf'^[{HANJA}]{{2,8}}\s*[.,]\s*', '', mean)
    mean = strip_lead(word, mean)
    # 양끝이 짝을 이룰 때만 따옴표를 벗긴다. 한쪽만 지우면 문장이 깨진다.
    m2 = re.match(r'^[\'"“‘](.+)[\'"”’]$', mean)
    if m2:
        mean = m2.group(1)
    mean = mean.strip()
    if len(mean) < 8:
        return None

    # 광고가 요청마다 바뀌어 키워드로 막을 수 없다. 대신 문장으로 끝나는 조각만
    # 취한다. 광고는 본문 뒤에 마침표 없이 붙으므로 이것만으로 떨어져 나간다.
    parts = [p for p in re.split(r'(?<=[.!?])\s+', mean) if p.rstrip().endswith(('.', '!', '?'))]
    if not parts:
        return None
    mean = ' '.join(parts[:2]).strip()
    if len(mean) > 200:
        mean = parts[0].strip()
    if len(mean) < 8:
        return None

    item = {"word": word, "mean": mean, "source": "namuwiki"}
    if hanja:
        item["hanja"] = hanja
    return item


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    todo = json.load(open(sys.argv[1], encoding="utf-8"))
    out_path = os.path.join(root, "data", "namu_sajaseongeo.json")

    got = {}
    if os.path.exists(out_path):
        got = {x["word"]: x for x in json.load(open(out_path, encoding="utf-8"))}
    rest = [w for w in todo if w not in got]
    print(f"전체 {len(todo)} / 이미 받음 {len(got)} / 남음 {len(rest)}", flush=True)

    fail = []
    for i, w in enumerate(rest, 1):
        h = fetch(w)
        it = parse(w, h) if h else None
        if it:
            got[w] = it
        else:
            fail.append(w)
        if i % 20 == 0 or i == len(rest):
            json.dump(sorted(got.values(), key=lambda x: x["word"]),
                      open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print(f"  {len(got)}/{len(todo)}  실패 {len(fail)}  마지막={w}", flush=True)
        time.sleep(DELAY)

    json.dump(sorted(got.values(), key=lambda x: x["word"]),
              open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"완료: {len(got)}개 (실패 {len(fail)}: {fail[:10]})")


if __name__ == "__main__":
    main()
