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

# ✅ 取得假名資料
def fetch_kana_info(kana):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT kana, image_url, stroke_order_text, audio_url FROM kana_items WHERE kana = %s", (kana,))
            row = cursor.fetchone()
            if row:
                return {
                    "kana": row[0],
                    "image_url": safe_url(row[1]),
                    "stroke_order_text": row[2],
                    "audio_url": safe_url(row[3])
                }
            return None
    finally:
        conn.close()

# ✅ 影像比對
def compare_images(user_img_path: str, correct_img_path: str) -> float:
    img1 = cv2.imread(user_img_path, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(correct_img_path, cv2.IMREAD_GRAYSCALE)
    if img1 is None or img2 is None:
        raise FileNotFoundError("❌ Unable to load image (user or sample)")
    img1, img2 = [cv2.resize(i, (200, 200)) for i in (img1, img2)]
    score, _ = ssim(img1, img2, full=True)
    return score

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
                TextSendMessage(text=f"📖 Stroke order description：\n{info['stroke_order_text']}"),
                ImageSendMessage(original_content_url=info['image_url'], preview_image_url=info['image_url']),
                AudioSendMessage(original_content_url=info['audio_url'], duration=3000),
            ]
            line_bot_api.reply_message(event.reply_token, messages)
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("❌ Data for the kana could not be found."))

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
