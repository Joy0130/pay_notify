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

TARGET_SENDER = 'ebill@ebppsmtp.taipower.com.tw'
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
    """處理新郵件，如果找到並發送了通知，則返回 True"""
    logging.info("正在檢查新郵件...")
    # 搜尋未讀且來自特定寄件人的郵件
    messages = client.search(['UNSEEN', 'FROM', TARGET_SENDER])
    if not messages:
        logging.info("沒有找到符合條件的新郵件。")
        return False

    notification_sent = False
    logging.info(f"找到 {len(messages)} 封新郵件，正在處理...")
    for msgid in messages:
        try:
            # 取得郵件內容
            # X-GM-MSGID 是 Gmail 專有的 ID，為十進位數字
            fetched_data = client.fetch(msgid, ['BODY[]', 'X-GM-MSGID'])
            raw_message = fetched_data[msgid][b'BODY[]']
            gmail_msg_id = fetched_data[msgid][b'X-GM-MSGID']
            msg = email.message_from_bytes(raw_message)
            
            # 解碼主旨
            subject, encoding = email.header.decode_header(msg['subject'])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or 'utf-8')

            if TARGET_SUBJECT_KEYWORD in subject:
                logging.info(f"找到電費通知郵件: {subject}")

                # 將 Gmail 的十進位 ID 轉換為十六進位，並移除 '0x' 前綴
                gmail_msg_id_hex = hex(gmail_msg_id)[2:]
                # 組成 Gmail 網址
                mail_url = f"https://mail.google.com/mail/u/0/#inbox/{gmail_msg_id_hex}"
                
                notification_message = f"收到電費通知:\n{subject}\n\n記得要繳費喔~\n點此查看信件:\n{mail_url}"
                send_line(notification_message)
                notification_sent = True

            # 將郵件標示為已讀
            client.add_flags(msgid, [b'\\Seen'])
        except Exception as e:
            logging.error(f"處理郵件 {msgid} 時發生錯誤: {e}")
    
    return notification_sent

def main():
    """主函式：連線到 Gmail，處理一次郵件，然後根據結果結束程式。"""
    notification_sent = False
    try:
        with IMAPClient(IMAP_HOST) as client:
            logging.info(f"登入 Gmail: {EMAIL_ACCOUNT}")
            client.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
            client.select_folder('INBOX')
            logging.info("登入成功，開始檢查郵件...")
            
            notification_sent = process_new_mail(client)

    except (IMAPClientError, OSError) as e:
        logging.error(f"IMAP 連線或處理時發生錯誤: {e}")

    if not notification_sent:
        logging.info("未發送任何通知，等待 3 秒後結束...")
        time.sleep(3)
    
    logging.info("任務完成，程式結束。")

if __name__ == "__main__":
    main()
