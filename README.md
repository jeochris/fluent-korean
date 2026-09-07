# 오늘의 한국어 슬랙 봇

매일 슬랙 채널에 사자성어 / 속담 / 관용구를 **뜻과 예문까지** 붙여서 올린다.

## 데이터

`data/daily_ko.json`

| 키 | 개수 | 뜻 | 예문 | 출처 |
|---|---|---|---|---|
| `sajaseongeo` | 345 | ✅ | 63% | 한국어기초사전 178 + 위키낱말사전 167 |
| `sokdam` | 656 | ✅ | 32% | 한국어기초사전 |
| `gwanyonggu` | 2,227 | ✅ | 81% | 한국어기초사전 |

한국어기초사전에는 사자성어가 178개뿐이라 각주구검·결초보은 같은 대표적인 것들이
빠져 있다. 위키낱말사전 `분류:한국어 한자성어` 에서 167개를 보충했다.

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

- 항목은 **섞어둔 순열을 순서대로** 꺼낸다. `EPOCH`(2026-09-07)부터 며칠 지났는지로 위치를 계산하므로
  상태 저장이 필요 없고, 같은 날 여러 번 실행해도 결과가 같다.
  목록을 한 바퀴 다 쓰면 다시 섞어서(회차 +1) 처음부터 돈다.
- 그래서 n개짜리 목록은 **정확히 n일 동안 중복이 없다**. 사자성어 345일, 속담 656일, 관용구 2,227일.
  (매일 새로 무작위로 뽑으면 생일 문제 때문에 178개로도 20일이면 중복이 난다.)
- `EPOCH` 를 바꾸면 전체 순서가 어긋나므로 건드리지 않는다.
- 뜻 아래에 예문이 있으면 인용 블록으로 붙는다. 예문은 항목에 따라 없을 수도 있다.
- 구성을 바꾸려면 `bot.py` 의 `DAILY` 리스트를 수정하면 된다.

## 라이선스

- 국립국어원 한국어기초사전: **CC BY-SA 2.0 KR**
- 위키낱말사전: **CC BY-SA 4.0**

둘 다 저작자표시-동일조건변경허락이다. 슬랙 메시지 하단에 그날 쓴 출처만 밝히고,
이 저장소는 CC BY-SA 4.0 으로 재배포한다.

## 데이터 만드는 순서

```bash
python scripts/extract_krdict.py      # 한국어기초사전 덤프에서 추출
python scripts/fetch_wiktionary.py    # 위키낱말사전 사자성어 보충
python scripts/normalize.py           # 병합·정리
```

- 사자성어는 네 글자만 남긴다 (`공상`, `면전` 같은 일반 한자어가 섞여 있다)
- 같은 표제어의 여러 뜻은 한 항목으로 합친다. 사전은 다의어를 뜻마다 따로 담고 있는데,
  그대로 두면 봇이 같은 말을 며칠 간격으로 다시 올리는 것처럼 보인다. 뜻은 최대 3개까지 번호를 붙여 나열한다.
