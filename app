from flask import Flask, request, jsonify, render_template, abort
import os, base64, cv2
from skimage.metrics import structural_similarity as ssim
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *

# ── 🔑 必填 ───────────────────────────
LINE_CHANNEL_ACCESS_TOKEN = "liqx01baPcbWbRF5if7oqBsZyf2+2L0eTOwvbIJ6f2Wec6is4sVd5onjl4fQAmc4n8EuqMfo7prlaG5la6kXb/y1gWOnk8ztwjjx2ZnukQbPJQeDwwcPEdFTOGOmQ1t88bQLvgQVczlzc/S9Q/6y5gdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET       = "cd9fbd2ce22b12f243c5fcd2d97e5680"
LIFF_URL                  = "https://liff.line.me/2007396139-Q0E29b2o"
# ────────────────────────────────────

# Flask 專案根目錄
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),  # 確保能找到 index.html
    static_folder=os.path.join(BASE_DIR, "static")
)

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static")
SAMPLE_FOLDER = os.path.join(BASE_DIR, "samples")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SAMPLE_FOLDER, exist_ok=True)

# ── 圖像相似度（SSIM）──────────────
def compare_images(user_img_path: str, correct_img_path: str) -> float:
    """讀取兩張圖片並以 SSIM 計算相似度，0~1 越高越像"""
    img1 = cv2.imread(user_img_path, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(correct_img_path, cv2.IMREAD_GRAYSCALE)
    if img1 is None or img2 is None:
        raise FileNotFoundError("❌ 無法載入圖片（user or sample）")
    img1, img2 = [cv2.resize(i, (200, 200)) for i in (img1, img2)]
    score, _ = ssim(img1, img2, full=True)
    return score
# ──────────────────────────────────

# ── LINE Bot init ──────────────────
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler      = WebhookHandler(LINE_CHANNEL_SECRET)
# ──────────────────────────────────

# ── Web UI ─────────────────────────
@app.route("/")
def home():
    """顯示前端畫板 (templates/index.html)"""
    return render_template("index.html")

@app.route("/check", methods=["POST"])
def check_image():
    """前端上傳 base64 圖片 + 正確答案，回傳比對結果"""
    data = request.json or {}
    image_data = data.get("image")
    answer     = data.get("answer")

    if not image_data or not answer:
        return jsonify({"correct": False, "error": "缺少 image 或 answer"}), 400

    # 儲存使用者圖片
    header, encoded = image_data.split(",", 1)
    user_img_path = os.path.join(UPLOAD_FOLDER, "user_input.png")
    with open(user_img_path, "wb") as f:
        f.write(base64.b64decode(encoded))

    correct_img_path = os.path.join(SAMPLE_FOLDER, f"{answer}.png")
    if not os.path.exists(correct_img_path):
        return jsonify({"correct": False, "error": f"找不到範例 {answer}.png"}), 404

    try:
        score = compare_images(user_img_path, correct_img_path)
        return jsonify({
            "correct": score > 0.6,
            "score"  : round(score, 3),
            "message": "✅ 答對！太棒了！" if score > 0.6 else "❌ 再試一次，加油！"
        })
    except Exception as e:
        return jsonify({"correct": False, "error": str(e)}), 500
# ──────────────────────────────────

# ── Kana Flex / Quick Reply 工具函式 ──────────────────

def kana_flex(category: str = "清音") -> dict:
    """依分類回傳平假名 Flex Carousel"""
    if category == "清音":
        rows = [
            "あ い う え お", "か き く け こ", "さ し す せ そ",
            "た ち つ て と", "な に ぬ ね の", "は ひ ふ へ ほ",
            "ま み む め も", "や   ゆ   よ", "ら り る れ ろ", "わ   を   ん",
        ]
    elif category == "濁音":
        rows = [
            "が ぎ ぐ げ ご", "ざ じ ず ぜ ぞ", "だ ぢ づ で ど", "ば び ぶ べ ぼ",
        ]
    elif category == "半濁音":
        rows = [
            "ぱ ぴ ぷ ぺ ぽ",
        ]
    else:
        rows = []

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
    return {"type": "carousel", "contents": bubbles}


def kana_category_quick_reply() -> QuickReply:
    """回傳『清音／濁音／半濁音』快速選單"""
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="清音", text="清音")),
        QuickReplyButton(action=MessageAction(label="濁音", text="濁音")),
        QuickReplyButton(action=MessageAction(label="半濁音", text="半濁音")),
    ])
# ─────────────────────────────────────────────

# ── LINE MessageEvent 處理 ──────────────────
@handler.add(MessageEvent, message=TextMessage)
def handle_msg(event):
    text = event.message.text.strip()

    # 0️⃣ 進入主功能選單
    if text == "我要練習":
        qr = QuickReply(items=[
            QuickReplyButton(action=URIAction(label="打開畫板", uri=LIFF_URL)),
            QuickReplyButton(action=MessageAction(label="平假名表", text="平假名表")),
            QuickReplyButton(action=MessageAction(label="幫助",      text="幫助")),
        ])
        line_bot_api.reply_message(event.reply_token, TextSendMessage("選擇功能👇", quick_reply=qr))

    # 1️⃣ 平假名表 → 顯示分類選單
    elif text == "平假名表":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage("請選擇：清音 / 濁音 / 半濁音", quick_reply=kana_category_quick_reply()),
        )

    # 2️⃣ 顯示對應分類的假名 Flex
    elif text in ("清音", "濁音", "半濁音"):
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text=f"平假名（{text}）", contents=kana_flex(text))
        )

    # 3️⃣ 幫助
    elif text == "幫助":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                "步驟：\n1️⃣ 輸入「我要練習」\n2️⃣ 點『打開畫板』作答\n3️⃣ 系統用 SSIM 判斷對錯 🎯"
            )
        )

    # 4️⃣ 其他輸入
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage("輸入「我要練習」來開始唷 ✍️"))
# ──────────────────────────────────

# ── LINE Webhook 入口 ───────────────────
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body      = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)  # 你可以先註解此行來暫停處理事件
    except InvalidSignatureError:
        abort(400)
    return "OK"
# ──────────────────────────────────

if __name__ == "__main__":
    # Render 預設 PORT 環境變數
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

