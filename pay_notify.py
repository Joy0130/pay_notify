from imapclient import IMAPClient
from imapclient.exceptions import IMAPClientError
import email, requests, os, time, logging
from dotenv import load_dotenv

# --- 設定日誌 (Logging) ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 載入環境變數 ---
load_dotenv()

# --- 常數定義 ---
IMAP_HOST = 'imap.gmail.com'
EMAIL_ACCOUNT = os.getenv('GMAIL_ACCOUNT')
EMAIL_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')

LINE_TOKEN = os.getenv('LINE_CHANNEL_TOKEN')
USER_ID = os.getenv('LINE_USER_ID')
LINE_API_URL = 'https://api.line.me/v2/bot/message/push'

TARGET_SENDER = 'gm10290014@gmail.com'
TARGET_SUBJECT_KEYWORD = '電費通知'

def send_line(msg):
    """發送 LINE Notify 訊息"""
    try:
        r = requests.post(
            LINE_API_URL,
            headers={
                'Authorization': f'Bearer {LINE_TOKEN}',
                'Content-Type': 'application/json'
            },
            json={'to': USER_ID, 'messages':[{'type':'text','text':msg}]},
            timeout=10  # 增加超時設定
        )
        if r.status_code != 200:
            logging.error(f"LINE 推播失敗: {r.status_code} - {r.text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"LINE 發送請求錯誤: {e}")

def process_new_mail(client):
    """處理新郵件"""
    logging.info("正在檢查新郵件...")
    # 搜尋未讀且來自特定寄件人的郵件
    messages = client.search(['UNSEEN', 'FROM', TARGET_SENDER])
    if not messages:
        logging.info("沒有找到符合條件的新郵件。")
        return

    logging.info(f"找到 {len(messages)} 封新郵件，正在處理...")
    for msgid in messages:
        try:
            # 取得郵件內容
            raw_message = client.fetch(msgid, ['BODY[]'])[msgid][b'BODY[]']
            msg = email.message_from_bytes(raw_message)
            
            # 解碼主旨
            subject, encoding = email.header.decode_header(msg['subject'])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or 'utf-8')

            if TARGET_SUBJECT_KEYWORD in subject:
                logging.info(f"找到電費通知郵件: {subject}")
                send_line(f"收到電費通知: {subject}")

            # 將郵件標示為已讀
            client.add_flags(msgid, [b'\\Seen'])
        except Exception as e:
            logging.error(f"處理郵件 {msgid} 時發生錯誤: {e}")

def main():
    """主函式，使用 IDLE 模式監控信箱"""
    while True:
        try:
            with IMAPClient(IMAP_HOST) as client:
                logging.info(f"登入 Gmail: {EMAIL_ACCOUNT}")
                client.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
                client.select_folder('INBOX')
                logging.info("登入成功，開始監控...")
                
                # 首次執行先檢查一次
                process_new_mail(client)

                # 進入 IDLE 模式，等待伺服器通知
                while True:
                    logging.info("進入 IDLE 模式，等待新郵件...")
                    client.idle()
                    responses = client.idle_check(timeout=600) # 每 10 分鐘檢查一次連線
                    client.idle_done()
                    if responses:
                        logging.info("伺服器回報有新活動，重新檢查郵件。")
                        process_new_mail(client)

        except (IMAPClientError, OSError) as e:
            logging.error(f"IMAP 連線錯誤: {e}")
            logging.info("將在 60 秒後嘗試重新連線...")
            time.sleep(60)

if __name__ == "__main__":
    main()
