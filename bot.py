#!/usr/bin/env python3
"""매일 사자성어·속담 하나씩과 관용구 두 개를 슬랙에 올린다."""
import hashlib
import json
import os
import random
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "daily_ko.json")

# (데이터 키, 라벨, 이모지, 개수)
DAILY = [
    ("sajaseongeo", "사자성어", "🀄", 1),
    ("sokdam", "속담", "🗣️", 1),
    ("gwanyonggu", "관용구", "💬", 2),
]

WEEKDAY = "월화수목금토일"

# 순열의 기준일. 이 날짜를 바꾸면 전체 순서가 어긋나므로 건드리지 않는다.
EPOCH = date(2026, 9, 7)


def _permutation(kind, round_no, n):
    """(종류, 회차) 로 결정되는 0..n-1 의 섞인 순서. 매번 같은 결과가 나온다."""
    seed = hashlib.sha256(f"{kind}:{round_no}".encode()).digest()
    order = list(range(n))
    random.Random(int.from_bytes(seed, "big")).shuffle(order)
    return order


def nth(items, kind, k):
    """무한 수열의 k번째 항목.

    항목을 매번 새로 뽑는 대신, 섞어둔 순서대로 하나씩 꺼낸다.
    n개를 다 쓰면 다시 섞어서(회차 +1) 처음부터 돌린다.
    덕분에 n개짜리 목록은 정확히 n일 동안 중복 없이 간다.
    """
    n = len(items)
    round_no, offset = divmod(k, n)
    return items[_permutation(kind, round_no, n)[offset]]


def pick(items, kind, day, n=1):
    """그날 나갈 n개. 같은 날엔 몇 번을 실행하든 같은 결과."""
    base = (day - EPOCH).days * n
    return [nth(items, kind, base + i) for i in range(n)]


def headline(item):
    # 원본 데이터에 앞뒤 공백이 섞여 있다. 볼드 마크업 안에 공백이 들어가면 슬랙이 렌더링하지 않는다.
    head = f"*{item['word'].strip()}*"
    hanja = (item.get("hanja") or "").strip()
    if hanja:
        head += f" ({hanja})"
    return head


def build_blocks(picks, day):
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "📚 오늘의 한국어", "emoji": True},
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"{day.strftime('%Y년 %m월 %d일')} ({WEEKDAY[day.weekday()]})",
                }
            ],
        },
        {"type": "divider"},
    ]

    for label, emoji, item in picks:
        lines = [f"{emoji}  {label}", headline(item), item["mean"].strip()]
        if item.get("example"):
            lines.append(f"> _{item['example'].strip()}_")
        blocks.append(
            {"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(lines)}}
        )

    return blocks


def post(webhook, payload):
    req = urllib.request.Request(
        webhook,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    with urllib.request.urlopen(req, timeout=20) as res:
        return res.status, res.read().decode()


def main():
    today = date.today() if "--local-date" in sys.argv else datetime.now(KST).date()
    for arg in sys.argv[1:]:
        if arg.startswith("--date="):
            today = date.fromisoformat(arg.split("=", 1)[1])

    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)

    picks = []
    for key, label, emoji, n in DAILY:
        # 누구나 아는 것(easy)과 직장 채널에 부적절한 것(blocked)은 올리지 않는다.
        pool = [x for x in data[key] if not x.get("easy") and not x.get("blocked")]
        for item in pick(pool, key, today, n):
            picks.append((label, emoji, item))

    summary = " · ".join(f"{lab} {it['word'].strip()}" for lab, _, it in picks)
    payload = {
        "text": f"📚 오늘의 한국어 — {summary}",  # 알림·미리보기용
        "blocks": build_blocks(picks, today),
    }

    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook or "--dry-run" in sys.argv:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        if not webhook:
            print("\n[SLACK_WEBHOOK_URL 이 없어서 전송하지 않음]", file=sys.stderr)
        return

    status, body = post(webhook, payload)
    print(f"slack {status}: {body}")


if __name__ == "__main__":
    main()
