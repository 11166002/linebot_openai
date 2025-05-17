from flask import Flask, request, jsonify, render_template, abort
import os, io
from google.cloud import vision
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *

# ── 🔑 必填 ───────────────────────────
LINE_CHANNEL_ACCESS_TOKEN = "liqx01baPcbWbRF5if7oqBsZyf2+2L0eTOwvbIJ6f2Wec6is4sVd5onjl4fQAmc4n8EuqMfo7prlaG5la6kXb/y1gWOnk8ztwjjx2ZnukQbPJQeDwwcPEdFTOGOmQ1t88bQLvgQVczlzc/S9Q/6y5gdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET       = "cd9fbd2ce22b12f243c5fcd2d97e5680"
LIFF_URL                  = "https://liff.line.me/2007396139-Q0E29b2o"
# ────────────────────────────────────

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"

app = Flask(__name__)
UPLOAD_FOLDER = "static"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── Google Vision OCR ─────────────────
def detect_kana(img_path: str) -> str:
    client = vision.ImageAnnotatorClient()
    with io.open(img_path, "rb") as f:
        content = f.read()
    image = vision.Image(content=content)
    res = client.text_detection(image=image)
    return res.text_annotations[0].description.strip() if res.text_annotations else "👀 沒找到假名，再寫一次吧！"
# ────────────────────────────────────

# ── LINE Bot init ───────────────────
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
# ────────────────────────────────────

# ── Web UI ──────────────────────────
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    if "image" not in request.files:
        return jsonify({"error": "請先選擇圖片！"}), 400
    f = request.files["image"]
    save_to = os.path.join(UPLOAD_FOLDER, "input.png")
    f.save(save_to)
    txt = detect_kana(save_to)
    return jsonify(
        {
            "recognized_text": f"🎌【Japan Learning Game】判定你寫的是：「{txt}」！🌟",
            "note": "📣 如果不是你想寫的，再試一次也沒關係，加油！",
        }
    )
# ────────────────────────────────────

# ── 假名分類邏輯 ─────────────────────
KANA_CATEGORIES = ["清音", "濁音", "半濁音"]

def kana_category_quick_reply():
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label=cat, text=cat))
        for cat in KANA_CATEGORIES
    ])

def build_kana_flex(category):
    kana_rows = {
        "清音": ["あ い う え お", "か き く け こ", "さ し す せ そ", "た ち つ て と", "な に ぬ ね の", "は ひ ふ へ ほ", "ま み む め も", "や   ゆ   よ", "ら り る れ ろ", "わ   を   ん"],
        "濁音": ["が ぎ ぐ げ ご", "ざ じ ず ぜ ぞ", "だ ぢ づ で ど", "ば び ぶ べ ぼ"],
        "半濁音": ["ぱ ぴ ぷ ぺ ぽ"]
    }
    rows = kana_rows.get(category, [])
    bubbles = [
        {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [{"type": "text", "text": r, "size": "xl", "align": "center"}],
            },
        }
        for r in rows
    ]
    return {
        "type": "carousel",
        "contents": bubbles
    }
# ────────────────────────────────────

# ── LINE Webhook ─────────────────────
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_msg(event):
    text = event.message.text.strip()

    if text == "我要練習":
        qr = QuickReply(items=[
            QuickReplyButton(action=URIAction(label="打開畫板", uri=LIFF_URL)),
            QuickReplyButton(action=MessageAction(label="平假名表", text="平假名表")),
            QuickReplyButton(action=MessageAction(label="幫助", text="幫助")),
        ])
        line_bot_api.reply_message(event.reply_token, TextSendMessage("選擇功能👇", quick_reply=qr))
        return

    # 第二層：平假名表 → 選分類
    if text == "平假名表":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage("請選擇：清音 / 濁音 / 半濁音", quick_reply=kana_category_quick_reply()),
        )
        return

    # 第三層：顯示指定分類的假名表
    if text in KANA_CATEGORIES:
        bubble = build_kana_flex(text)
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text=f"{text} 假名表", contents=bubble),
        )
        return

    if text == "幫助":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage("輸入「我要練習」→ 點打開畫板 → 上傳手寫假名圖片。")
        )
        return

    # 預設回應
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage("輸入「我要練習」來開始唷 ✍️")
    )
# ────────────────────────────────────

# ── Flask 啟動 ───────────────────────
if __name__ == "__main__":
    app.run(debug=True)
