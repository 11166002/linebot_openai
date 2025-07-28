from flask import Flask, request, jsonify, render_template, abort
import os, base64, cv2
from skimage.metrics import structural_similarity as ssim
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import mysql.connector
from mysql.connector import Error

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

def compare_images(user_img_path: str, correct_img_path: str) -> float:
    img1 = cv2.imread(user_img_path, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(correct_img_path, cv2.IMREAD_GRAYSCALE)
    if img1 is None or img2 is None:
        raise FileNotFoundError("❌ Unable to load image (user or sample)")
    img1, img2 = [cv2.resize(i, (200, 200)) for i in (img1, img2)]
    score, _ = ssim(img1, img2, full=True)
    return score

# ✅ 加入這段：資料庫連線函式
def get_db_connection():
    return mysql.connector.connect(
        host="192.168.0.57",           # ✅ 請修改為你的主機名稱
        user="root",                # ✅ 你的 MySQL 使用者帳號
        password="0813",   # ✅ 你的 MySQL 密碼
        database="kana_library",    # ✅ 資料庫名稱
        charset='utf8mb4'
    )

# ✅ LINE BOT 初始化
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
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM kana_items WHERE kana = %s", (text,))
        row = cursor.fetchone()
        conn.close()

        if row:
            flex = {
                "type": "bubble",
                "size": "mega",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"{row['kana']} - Stroke Order",
                            "weight": "bold",
                            "size": "xl",
                            "margin": "md"
                        },
                        {
                            "type": "image",
                            "url": row["image_url"],
                            "size": "full",
                            "aspectMode": "fit",
                            "margin": "md"
                        },
                        {
                            "type": "text",
                            "text": row["stroke_order_text"],
                            "wrap": True,
                            "margin": "md"
                        },
                        {
                            "type": "button",
                            "action": {
                                "type": "uri",
                                "label": "▶ 聽發音",
                                "uri": row["audio_url"]
                            },
                            "style": "primary",
                            "margin": "md"
                        }
                    ]
                }
            }
            line_bot_api.reply_message(
                event.reply_token,
                FlexSendMessage(alt_text=f"{row['kana']} 的筆順資料", contents=flex)
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage("⚠️ 找不到資料，請確認是否有輸入正確假名。")
            )

    except Exception as e:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(f"❌ 發生錯誤：{str(e)}")
        )


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body      = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"
