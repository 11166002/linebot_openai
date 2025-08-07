from flask import Flask, request, jsonify, render_template, abort
import os, base64, cv2, psycopg2
from urllib.parse import quote
from skimage.metrics import structural_similarity as ssim
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *

# ── 🔑 Required ───────────────────────────
LINE_CHANNEL_ACCESS_TOKEN = "liqx01baPcbWbRF5if7oqBsZyf2+2L0eTOwvbIJ6f2Wec6is4sVd5onjl4fQAmc4n8EuqMfo7prlaG5la6kXb/y1gWOnk8ztwjjx2ZnukQbPJQeDwwcPEdFTOGOmQ1t88bQLvgQVczlzc/S9Q/6y5gdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET       = "cd9fbd2ce22b12f243c5fcd2d97e5680"
LIFF_URL                  = "https://liff.line.me/2007396139-Q0E29b2o"
# ─────────────────────────────────────────

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static")
SAMPLE_FOLDER = os.path.join(BASE_DIR, "samples")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SAMPLE_FOLDER, exist_ok=True)

# ✅ URL 編碼，確保 LINE API 能接受
def safe_url(url: str) -> str:
    return quote(url, safe=":/")

# ✅ PostgreSQL 資料庫連線設定（Render 資料庫資訊）
def get_db_connection():
    return psycopg2.connect(
        host="dpg-d29lgk2dbo4c73bmamsg-a.oregon-postgres.render.com",        # 例: dpg-xxxxxxx.render.com
        port="5432",
        database="japan_2tmc",        # 你建立的資料庫名稱
        user="japan_2tmc_user",
        password="wjEjoFXbdPA8WYTJTkg0mI5oR02ozdnI"
    )

# ✅ URL 修正邏輯（轉 raw 並編碼）
def fix_url(url):
    if url.startswith("https://github.com/11166002/audio-files/blob/main/"):
        url = url.replace(
            "https://github.com/11166002/audio-files/blob/main/",
            "https://raw.githubusercontent.com/11166002/audio-files/main/"
        )
    return quote(url, safe=":/")

# ✅ 檢查圖片/音檔是否可讀取
def is_valid_url(url):
    try:
        r = requests.get(url, timeout=5)
        return r.status_code == 200 and 'image' in r.headers.get("Content-Type", "") or 'audio' in r.headers.get("Content-Type", "")
    except:
        return False

# ✅ 路由：訪問這個網址會修正 image_url 與 audio_url 並檢查有效性
@app.route("/fix_urls")
def fix_urls():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, image_url, audio_url FROM kana_items")
    rows = cursor.fetchall()

    updated = 0
    skipped = 0
    for id_, img_url, aud_url in rows:
        if not img_url and not aud_url:
            continue

        fixed_img = fix_url(img_url) if img_url else img_url
        fixed_aud = fix_url(aud_url) if aud_url else aud_url

        valid_img = is_valid_url(fixed_img) if fixed_img else True
        valid_aud = is_valid_url(fixed_aud) if fixed_aud else True

        if not valid_img or not valid_aud:
            skipped += 1
            continue

        if fixed_img != img_url or fixed_aud != aud_url:
            cursor.execute(
                "UPDATE kana_items SET image_url = %s, audio_url = %s WHERE id = %s",
                (fixed_img, fixed_aud, id_)
            )
            updated += 1

    conn.commit()
    cursor.close()
    conn.close()

    return f"✅ 修正完成，共更新 {updated} 筆，跳過無效連結 {skipped} 筆。"

# LINE Bot 初始化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler      = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/check", methods=["POST"])
def check_image():
    data = request.json or {}
    image_data = data.get("image")
    answer     = data.get("answer")

    if not image_data or not answer:
        return jsonify({"correct": False, "error": "Missing image or answer"}), 400

    header, encoded = image_data.split(",", 1)
    user_img_path = os.path.join(UPLOAD_FOLDER, "user_input.png")
    with open(user_img_path, "wb") as f:
        f.write(base64.b64decode(encoded))

    correct_img_path = os.path.join(SAMPLE_FOLDER, f"{answer}.png")
    if not os.path.exists(correct_img_path):
        return jsonify({"correct": False, "error": f"Sample {answer}.png not found"}), 404

    try:
        score = compare_images(user_img_path, correct_img_path)
        return jsonify({
            "correct": score > 0.6,
            "score"  : round(score, 3),
            "message": "✅ Correct! Great job!" if score > 0.6 else "❌ Try again!"
        })
    except Exception as e:
        return jsonify({"correct": False, "error": str(e)}), 500

def kana_flex(category: str = "Seion") -> dict:
    if category == "Seion":
        rows = [
            "あ い う え お", "か き く け こ", "さ し す せ そ",
            "た ち つ て と", "な に ぬ ね の", "は ひ ふ へ ほ",
            "ま み む め も", "や ゆ よ", "ら り る れ ろ", "わ を ん",
        ]
    elif category == "Dakuon":
        rows = [
            "が ぎ ぐ げ ご", "ざ じ ず ぜ ぞ", "だ ぢ づ で ど", "ば び ぶ べ ぼ",
        ]
    elif category == "Handakuon":
        rows = [
            "ぱ ぴ ぷ ぺ ぽ",
        ]
    else:
        rows = []

    bubbles = []
    for row in rows:
        bubble = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": row.strip(),
                            "text": row.strip()
                        },
                        "style": "primary",
                        "height": "sm"
                    }
                ]
            }
        }
        bubbles.append(bubble)

    return {"type": "carousel", "contents": bubbles}

def generate_kana_buttons(row: str) -> dict:
    kana_list = row.strip().split()
    bubbles = []
    for kana in kana_list:
        bubble = {
            "type": "bubble",
            "size": "micro",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": kana,
                            "text": kana
                        },
                        "style": "primary",
                        "height": "sm"
                    }
                ]
            }
        }
        bubbles.append(bubble)
    return {"type": "carousel", "contents": bubbles}

@handler.add(MessageEvent, message=TextMessage)
def handle_msg(event):
    text = event.message.text.strip()

    if text == "Start Practice":
        qr = QuickReply(items=[
            QuickReplyButton(action=URIAction(label="Open Canvas", uri=LIFF_URL)),
            QuickReplyButton(action=MessageAction(label="Kana Table", text="Kana Table")),
            QuickReplyButton(action=MessageAction(label="Help", text="Help")),
        ])
        line_bot_api.reply_message(event.reply_token, TextSendMessage("Choose a function 👇", quick_reply=qr))

    elif text == "Kana Table":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage("Please choose: Seion / Dakuon / Handakuon", quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="Seion", text="Seion")),
                QuickReplyButton(action=MessageAction(label="Dakuon", text="Dakuon")),
                QuickReplyButton(action=MessageAction(label="Handakuon", text="Handakuon")),
            ])),
        )

    elif text in ("Seion", "Dakuon", "Handakuon"):
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text=f"Kana ({text})", contents=kana_flex(text))
        )

    elif text in [
        "あ い う え お", "か き く け こ", "さ し す せ そ",
        "た ち つ て と", "な に ぬ ね の", "は ひ ふ へ ほ",
        "ま み む め も", "や ゆ よ", "ら り る れ ろ", "わ を ん",
        "が ぎ ぐ げ ご", "ざ じ ず ぜ ぞ", "だ ぢ づ で ど", "ば び ぶ べ ぼ",
        "ぱ ぴ ぷ ぺ ぽ"
    ]:
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text="Select a kana", contents=generate_kana_buttons(text))
        )

    elif text in [
        "あ", "い", "う", "え", "お",
        "か", "き", "く", "け", "こ",
        "さ", "し", "す", "せ", "そ",
        "た", "ち", "つ", "て", "と",
        "な", "に", "ぬ", "ね", "の",
        "は", "ひ", "ふ", "へ", "ほ",
        "ま", "み", "む", "め", "も",
        "や", "ゆ", "よ",
        "ら", "り", "る", "れ", "ろ",
        "わ", "を", "ん",
        "が", "ぎ", "ぐ", "げ", "ご",
        "ざ", "じ", "ず", "ぜ", "ぞ",
        "だ", "ぢ", "づ", "で", "ど",
        "ば", "び", "ぶ", "べ", "ぼ",
        "ぱ", "ぴ", "ぷ", "ぺ", "ぽ"
    ]:
        info = fetch_kana_info(text)
        if info:
            messages = [
                TextSendMessage(text=f"📖 筆順說明：\n{info['stroke_order_text']}"),
                ImageSendMessage(original_content_url=info['image_url'], preview_image_url=info['image_url']),
                AudioSendMessage(original_content_url=info['audio_url'], duration=3000),
            ]
            line_bot_api.reply_message(event.reply_token, messages)
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("❌ 無法找到該假名的資料"))

    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage("Type 'Start Practice' to begin ✍️"))

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body      = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"
