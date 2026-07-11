# Pay Notify 繳費通知機器人

自動偵測 Gmail 信箱中的電費、瓦斯費繳費通知信件，並透過 LINE Messaging API 推播提醒，避免忘記繳費。

## 功能特色

- 透過 IMAP 連線 Gmail，掃描**未讀信件**中符合條件的繳費通知
- 依「寄件人 + 主旨關鍵字」比對，目前支援：
  - 台灣電力公司電費通知（`ebill@ebppsmtp.taipower.com.tw`，主旨含「電費通知」）
  - 欣欣天然氣瓦斯費通知（`shinshingas@fecorp.biz`，主旨含「電子繳費通知單」）
- 找到符合條件的信件後，透過 LINE 推播訊息（含信件連結），並將信件標示為已讀
- 搭配 GitHub Actions 排程，於帳單常見的寄送時段自動執行，也可手動觸發

## 專案結構

- [pay_notify.py](pay_notify.py) — 主程式：登入 Gmail、搜尋信件、比對關鍵字、發送 LINE 通知
- [requirements.txt](requirements.txt) — Python 相依套件
- [.github/workflows/main.yaml](.github/workflows/main.yaml) — GitHub Actions 排程設定

## 事前準備

1. **Gmail 應用程式密碼**
   - 需先在 Google 帳戶開啟兩步驟驗證，並產生一組「應用程式密碼」供 IMAP 登入使用（不可使用一般登入密碼）。
2. **LINE Messaging API**
   - 需建立一個 LINE Bot（Messaging API channel），取得 Channel Access Token。
   - 取得你要接收通知的 `User ID`（可透過 LINE Bot Webhook 或官方工具查詢）。

## 環境變數設定

程式透過 `.env` 檔（本機執行）或 GitHub Actions Secrets（自動化執行）讀取以下變數：

| 變數名稱 | 說明 |
| --- | --- |
| `GMAIL_ACCOUNT` | 要監控的 Gmail 帳號 |
| `GMAIL_APP_PASSWORD` | Gmail 應用程式密碼 |
| `LINE_CHANNEL_TOKEN` | LINE Messaging API 的 Channel Access Token |
| `LINE_USER_ID` | 接收通知的 LINE User ID |

本機執行時，可在專案根目錄建立 `.env` 檔：

```env
GMAIL_ACCOUNT=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password
LINE_CHANNEL_TOKEN=your_line_channel_token
LINE_USER_ID=your_line_user_id
```

## 本機執行

```bash
pip install -r requirements.txt
python pay_notify.py
```

## 自動化執行（GitHub Actions）

`.github/workflows/main.yaml` 已設定排程，會在每兩個月一期帳單常見的寄送區間（每年單數月的 1～11 號及 16～19 號，對應台灣時間早上 07:30～07:59 與下午 16:00～16:15）每 5 分鐘檢查一次，亦可於 GitHub Actions 頁面手動觸發（`workflow_dispatch`）。

使用前請在 GitHub Repository 的 **Settings → Secrets and variables → Actions** 設定以下 Secrets：

- `GMAIL_ACCOUNT`
- `GMAIL_APP_PASSWORD`
- `LINE_CHANNEL_TOKEN`
- `LINE_USER_ID`

## 自訂寄件人與關鍵字

可修改 [pay_notify.py](pay_notify.py) 中的 `TARGET_SENDERS`、`TARGET_SUBJECT_KEYWORDS` 常數及 `process_new_mail()` 內的判斷邏輯，擴充支援其他帳單來源。
