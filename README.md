# 오늘의 한국어 슬랙 봇

매일 슬랙 채널에 사자성어 / 속담 / 관용구를 **뜻과 예문까지** 붙여서 올린다.

## 데이터

`data/daily_ko.json`

| 키 | 개수 | 뜻 | 예문 | 출처 |
|---|---|---|---|---|
| `sajaseongeo` | 1,047 | ✅ | 일부 | 나무위키 크롤링 + 한국어기초사전(207개 덮어씀) |
| `sokdam` | 704 | ✅ | 일부 | 국립국어원 한국어기초사전 |
| `gwanyonggu` | 2,493 | ✅ | 대부분 | 국립국어원 한국어기초사전 |

각 항목: `word`, `mean`, 그리고 선택적으로 `hanja`, `example`, `pos`, `category`, `level`.

### 데이터 재생성

```bash
curl -L -A "Mozilla/5.0" -H "Referer: https://krdict.korean.go.kr/download/downloadPopup" \
  "https://krdict.korean.go.kr/dicBatchDownload?seq=214" -o krdict.zip
unzip krdict.zip -d krdict
python scripts/extract_krdict.py
```

한국어기초사전 전체 덤프는 **로그인 없이** 받을 수 있다(84MB zip → 969MB json, 11개 파일).
`seq=212` 엑셀 / `213` XML / `214` JSON.

## 설치

1. **슬랙 Incoming Webhook 만들기**
   - https://api.slack.com/apps → Create New App → From scratch
   - Incoming Webhooks → 활성화 → Add New Webhook to Workspace → 채널 선택
   - `https://hooks.slack.com/services/...` URL 복사

2. **GitHub 레포에 secret 등록**
   - Settings → Secrets and variables → Actions → New repository secret
   - 이름 `SLACK_WEBHOOK_URL`, 값은 위 URL

3. push 하면 끝. 매일 09:00 KST 에 올라간다.

## 로컬 테스트

```bash
python bot.py --dry-run           # 전송 없이 payload 만 출력
python bot.py --date=2026-12-25   # 특정 날짜에 뭐가 나갈지 미리보기
SLACK_WEBHOOK_URL=... python bot.py
```

## 동작 방식

매일 09:00 KST 에 **한 개의 메시지**로 3개 항목을 올린다.

| 순서 | 종류 | 개수 |
|---|---|---|
| 1 | 🀄 사자성어 | 1 |
| 2 | 🗣️ 속담 | 1 |
| 3 | 💬 관용구 | 1 |

"어려운 단어"(한국어기초사전 고급 어휘 46,957개)는 빼 두었다. 필요하면
`scripts/extract_krdict.py` 로 다시 뽑아 `data/daily_ko.json` 에 `word` 키로 넣고,
`bot.py` 의 `DAILY` 에 `("word", "어려운 단어", "📖", 2)` 를 추가하면 된다.

- 항목은 `sha256(종류 + 날짜 + 순번)` 으로 고른다. 같은 날 여러 번 실행해도 같은 게 나오고,
  별도 상태 저장이 필요 없다. 대신 완전한 순회는 아니라서 드물게 중복이 나올 수 있다.
- 뜻 아래에 예문이 있으면 인용 블록으로 붙는다. 예문은 항목에 따라 없을 수도 있다.
- 구성을 바꾸려면 `bot.py` 의 `DAILY` 리스트를 수정하면 된다.

## 라이선스 주의

- 국립국어원 한국어기초사전 / 우리말샘: **CC BY-SA 2.0 KR** — 출처만 밝히면 상업적 이용 포함 자유.
- 나무위키 출처 사자성어(840개): **CC BY-NC-SA 2.0 KR** — 비상업적 이용만 가능. 사내 슬랙은 괜찮지만
  외부 상업 서비스로 쓸 거면 이 840개를 빼거나 표준국어대사전 API로 대체할 것.
