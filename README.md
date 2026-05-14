# ITNews 每日資安推播

每天早上 08:00（台灣時間）抓 RSS / NVD CVE，分類後推到 Discord 與 Telegram。

## 功能

- 來源：The Hacker News、Bleeping Computer、Krebs on Security、Dark Reading、SecurityWeek、iThome 資安、NVD CVE feed
- 用關鍵字字典自動加標籤（`#零日`、`#漏洞`、`#勒索軟體`、`#APT`、`#資料外洩`、`#供應鏈`、`#CVE`、`#補丁`、`#惡意軟體`、`#釣魚`、`#雲端`、`#Web`、`#行動裝置`、`#工具`）
- 依標籤權重排序，每次最多推 20 條
- `state/seen.json` 紀錄已推連結，30 天內不重複

## 專案結構

```
ITNews/
├── .github/workflows/daily.yml   # 每日排程
├── src/
│   ├── main.py                   # 入口
│   ├── config.py                 # 來源、標籤字典
│   ├── fetchers/{rss,nvd}.py
│   ├── classifier.py
│   ├── dedup.py
│   └── notifiers/{discord,telegram}.py
├── state/seen.json               # 已推紀錄（自動 commit）
├── requirements.txt
└── .env.example
```

## 本機跡試

```powershell
# 1. 建虛擬環境
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. 複製 .env.example 為 .env，填入秘鑰
copy .env.example .env
# 編輯 .env，至少填 DISCORD_WEBHOOK_URL 或 TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID
# 想先看抓到什麼但不真的推：DRY_RUN=1

# 3. 跑
python -m src.main
```

### 取得 Discord Webhook

1. 開 Discord，到要推的頻道 → 齒輪「編輯頻道」→ 整合 → Webhook → 新增 Webhook
2. 複製 Webhook URL 貼到 `.env` 的 `DISCORD_WEBHOOK_URL`

### 取得 Telegram Bot Token 與 Chat ID

1. 在 Telegram 找 `@BotFather`，輸入 `/newbot` 依指示建立，拿到 token
2. 把 bot 加進你要推的群組（或直接和 bot 對話一句 hi）
3. 開 `https://api.telegram.org/bot<token>/getUpdates`，從回應裡找到 `chat.id`
   - 個人對話：正整數
   - 群組：負整數（含 `-100` 前綴）
4. token / chat_id 分別填到 `.env`

## 上 GitHub Actions

1. 把整個專案 push 到 GitHub repo
2. Repo → Settings → Secrets and variables → Actions → New repository secret，依序加：
   - `DISCORD_WEBHOOK_URL`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
3. Repo → Actions → 「Daily ITNews Push」→ Run workflow（手動觸發測試一次）
4. 之後每天 UTC 00:00（台灣 08:00）會自動跑

> Workflow 跑完會把 `state/seen.json` commit 回 repo；需要在 Repo → Settings → Actions → General → Workflow permissions 開啟 **Read and write permissions**。

## 環境變數

| 變數 | 必填 | 預設 | 說明 |
|------|------|------|------|
| `DISCORD_WEBHOOK_URL` | 二擇一 | - | Discord webhook |
| `TELEGRAM_BOT_TOKEN` | 二擇一 | - | Telegram bot token |
| `TELEGRAM_CHAT_ID` | 與 token 成組 | - | 推送對象 chat id |
| `DRY_RUN` | 否 | `0` | `1` 只列印不推播 |
| `MAX_ITEMS` | 否 | `20` | 每次最多推幾條 |
| `LOOKBACK_HOURS` | 否 | `36` | 抓多少小時內的新文章 |

## 調整標籤 / 來源

- 新增來源：編輯 [src/config.py](src/config.py) 的 `RSS_SOURCES`
- 改標籤關鍵字 / 權重：編輯 `TAG_RULES`，數字越大越優先
- 改 NVD 過濾門檻：改 `NVD_MIN_CVSS`
