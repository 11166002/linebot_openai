from flask import Flask, request, jsonify, render_template, abort
import os, io, base64, cv2                         # ⚡️ 新增 base64 、cv2
from skimage.metrics import structural_similarity as ssim  # ⚡️ 新增 SSIM

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *

# ── 🔑 必填 ───────────────────────────
LINE_CHANNEL_ACCESS_TOKEN = "你的 TOKEN"
LINE_CHANNEL_SECRET       = "你的 SECRET"
LIFF_URL                  = "https://liff.line.me/xxxxxxxx"
# ────────────────────────────────────

app = Flask(__name__)
UPLOAD_FOLDER = "static"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── 圖像相似度比對（SSIM）──────────────
def compare_images(user_img_path: str, correct_img_path: str) -> float:
    img1 = cv2.imread(user_img_path, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(correct_img_path, cv2.IMREAD_GRAYSCALE)
    if img1 is None or img2 is None:
        raise FileNotFoundError("❌ 找不到範例圖！")
    img1 = cv2.resize(img1, (200, 200))
    img2 = cv2.resize(img2, (200, 200))
    score, _ = ssim(img1, img2, full=True)
    return score
# ────────────────────────────────────

# ── LINE Bot init ───────────────────
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler      = WebhookHandler(LINE_CHANNEL_SECRET)
# ────────────────────────────────────

# ── Web UI ──────────────────────────
@app.route("/")
def home():
    return render_template("index.html")

# Canvas base64 → SSIM 比對
@app.route("/check", methods=["POST"])
def check_image():
    data = request.json or {}
    image_data = data.get("image")
    answer     = data.get("answer")

    if not image_data or not answer:
        return jsonify({"correct": False, "error": "缺少 image 或 answer"}), 400

    # 儲存使用者圖片
    header, encoded = image_data.split(",", 1)
    img_bytes = base64.b64decode(encoded)
    user_img_path = os.path.join(UPLOAD_FOLDER, "user_input.png")
    with open(user_img_path, "wb") as f:
        f.write(img_bytes)

    correct_img_path = f"samples/{answer}.png"
    try:
        score = compare_images(user_img_path, correct_img_path)
        print(f"[SSIM] {answer} 分數：{score:.3f}")
        return jsonify({
            "correct": score > 0.6,
            "score"  : round(score, 3),
            "message": "✅ 答對！太棒了！" if score > 0.6 else "❌ 再試一次，加油！"
        })
    except Exception as e:
        return jsonify({"correct": False, "error": str(e)}), 500
# ────────────────────────────────────

# ── LINE Webhook ─────────────────────
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body      = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

def kana_flex():
    rows = [
        "あ い う え お", "か き く け こ", "さ し す せ そ",
        "た ち つ て と", "な に ぬ ね の", "は ひ ふ へ ほ",
        "ま み む め も", "や   ゆ   よ",   "ら り る れ ろ", "わ   を   ん",
    ]
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
    return {"type": "carousel", "contents": bubbles[:10]}

@handler.add(MessageEvent, message=TextMessage)
def handle_msg(event):
    text = event.message.text.strip()
    if text == "我要練習":
        qr = QuickReply(items=[
            QuickReplyButton(action=URIAction(label="打開畫板", uri=LIFF_URL)),
            QuickReplyButton(action=MessageAction(label="平假名表", text="平假名表")),
            QuickReplyButton(action=MessageAction(label="幫助",      text="幫助")),
        ])
        line_bot_api.reply_message(event.reply_token, TextSendMessage("選擇功能👇", quick_reply=qr))
    elif text == "平假名表":
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text="平假名 50 音", contents=kana_flex())
        )
    elif text == "幫助":
        line_bot_api.reply_message(event.reply_token, TextSendMessage(
            "步驟：\n1️⃣ 輸入「我要練習」\n2️⃣ 點『打開畫板』畫出題目\n3️⃣ 按送出，系統用 SSIM 判斷對錯 🎯"
        ))
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage("輸入「我要練習」來開始唷 ✍️"))

# ────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
