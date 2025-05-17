from flask import Flask, request, jsonify, render_template, abort
import os, base64, cv2
from skimage.metrics import structural_similarity as ssim
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *

# ── 🔑 LINE 設定 ───────────────────────────
LINE_CHANNEL_ACCESS_TOKEN = "liqx01baPcbWbRF5if7oqBsZyf2+2L0eTOwvbIJ6f2Wec6is4sVd5onjl4fQAmc4n8EuqMfo7prlaG5la6kXb/y1gWOnk8ztwjjx2ZnukQbPJQeDwwcPEdFTOGOmQ1t88bQLvgQVczlzc/S9Q/6y5gdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET       = "cd9fbd2ce22b12f243c5fcd2d97e5680"
LIFF_URL                  = "https://liff.line.me/2007396139-Q0E29b2o"
# ───────────────────────────────────────────

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, "templates"),
            static_folder=os.path.join(BASE_DIR, "static"))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static")
SAMPLE_FOLDER = os.path.join(BASE_DIR, "samples")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SAMPLE_FOLDER, exist_ok=True)

# ── 圖像相似度（SSIM）──────────────

def compare_images(user_img_path: str, correct_img_path: str) -> float:
    """Return SSIM score between two images."""
    img1 = cv2.imread(user_img_path, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(correct_img_path, cv2.IMREAD_GRAYSCALE)
    if img1 is None or img2 is None:
        raise FileNotFoundError("❌ 無法載入圖片（user or sample）")
    img1, img2 = [cv2.resize(i, (200, 200)) for i in (img1, img2)]
    score, _ = ssim(img1, img2, full=True)
    return score

# ── LINE Bot 初始化 ─────────────────
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ── Kana 資料（1 行 1 個：假名 + 羅馬音）─────
KANA_CATEGORIES = {
    "清音": [
        ("あ", "a"), ("い", "i"), ("う", "u"), ("え", "e"), ("お", "o"),
        ("か", "ka"), ("き", "ki"), ("く", "ku"), ("け", "ke"), ("こ", "ko"),
        ("さ", "sa"), ("し", "shi"), ("す", "su"), ("せ", "se"), ("そ", "so"),
        ("た", "ta"), ("ち", "chi"), ("つ", "tsu"), ("て", "te"), ("と", "to"),
        ("な", "na"), ("に", "ni"), ("ぬ", "nu"), ("ね", "ne"), ("の", "no"),
        ("は", "ha"), ("ひ", "hi"), ("ふ", "fu"), ("へ", "he"), ("ほ", "ho"),
        ("ま", "ma"), ("み", "mi"), ("む", "mu"), ("め", "me"), ("も", "mo"),
        ("や", "ya"), ("ゆ", "yu"), ("よ", "yo"),
        ("ら", "ra"), ("り", "ri"), ("る", "ru"), ("れ", "re"), ("ろ", "ro"),
        ("わ", "wa"), ("を", "wo"), ("ん", "n"),
    ],
    "濁音": [
        ("が", "ga"), ("ぎ", "gi"), ("ぐ", "gu"), ("げ", "ge"), ("ご", "go"),
        ("ざ", "za"), ("じ", "ji"), ("ず", "zu"), ("ぜ", "ze"), ("ぞ", "zo"),
        ("だ", "da"), ("ぢ", "ji"), ("づ", "zu"), ("で", "de"), ("ど", "do"),
        ("ば", "ba"), ("び", "bi"), ("ぶ", "bu"), ("べ", "be"), ("ぼ", "bo"),
    ],
    "半濁音": [
        ("ぱ", "pa"), ("ぴ", "pi"), ("ぷ", "pu"), ("ぺ", "pe"), ("ぽ", "po"),
    ],
}


def build_kana_flex(category: str) -> dict:
    pairs = KANA_CATEGORIES.get(category, [])
    pages = [pairs[i:i + 10] for i in range(0, len(pairs), 10)]
    bubbles = []

    for page in pages:
        contents = [
            {"type": "text", "text": f"{category}：請點選任一假名👇", "weight": "bold", "align": "center"}]
        for kana, romaji in page:
            contents.append({
                "type": "button",
                "action": {
                    "type": "message",
                    "label": f"{kana} | {romaji}",
                    "text": kana
                },
                "style": "primary",
                "margin": "sm"
            })
        bubbles.append({
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": contents
            }
        })

    return {
        "type": "carousel",
        "contents": bubbles
    }
    }


def kana_category_quick_reply() -> QuickReply:
    items = [QuickReplyButton(action=MessageAction(label=cat, text=cat)) for cat in KANA_CATEGORIES]
    return QuickReply(items=items)

# ── Web UI ─────────────────────────
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/check", methods=["POST"])
def check_image():
    data = request.json or {}
    image_data = data.get("image")
    answer = data.get("answer")
    if not image_data or not answer:
        return jsonify({"correct": False, "error": "缺少 image 或 answer"}), 400

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
            "score": round(score, 3),
            "message": "✅ 答對！太棒了！" if score > 0.6 else "❌ 再試一次，加油！",
        })
    except Exception as e:
        return jsonify({"correct": False, "error": str(e)}), 500

# ── LINE Webhook ───────────────────
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_msg(event):
    KANA_INFO = {
        "あ": ("a", "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7).m4a", "這個音是母音之一，例如：あさ（早上）"),
        "い": ("i", "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7)1.m4a", "這是日語的第二個母音，例如：いぬ（狗）"),
        "う": ("u", "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7)2.m4a", "第三個母音，例如：うみ（海）"),
        "え": ("e", "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7)3.m4a", "第四個母音，例如：えき（車站）"),
        "お": ("o", "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7)4.m4a", "第五個母音，例如：おちゃ（茶）"),
        "か": ("ka", "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7)5.m4a", "這是清音之一，例如：かさ（雨傘）")
    }

    text = event.message.text.strip()

    if text in KANA_INFO:
        romaji, audio_url, description = KANA_INFO[text]
        messages = [
            TextSendMessage(text=f"日語：{text}
羅馬拼音：{romaji}
說明：{description}"),
            AudioSendMessage(original_content_url=audio_url, duration=2000)
        ]
        line_bot_api.reply_message(event.reply_token, messages)
        return
    text = event.message.text.strip()

    # 主選單
    if text == "我要練習":
        qr = QuickReply(items=[
            QuickReplyButton(action=URIAction(label="打開畫板", uri=LIFF_URL)),
            QuickReplyButton(action=MessageAction(label="平假名表", text="平假名表")),
            QuickReplyButton(action=MessageAction(label="幫助", text="幫助")),
        ])
        line_bot_api.reply_message(event.reply_token, TextSendMessage("選擇功能👇", quick_reply=qr))
        return

    # 二階：平假名表 → 選分類
    if text == "平假名表":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage("請選擇：清音 / 濁音 / 半濁音", quick_reply=kana_category_quick_reply()),
        )
        return

    # 三階：顯示指定分類
    if text in KANA_CATEGORIES:
        bubble = build_kana_flex(text)
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text=f"{text} 假名表", contents=bubble),
        )
        return

    # 幫助
    if text == "幫助":
        help_msg = (
            "步驟：\n"
            "1️⃣ 輸入『我要練習』\n"
            "2️⃣ 點『打開畫板』開始寫字答題\n"
            "3️⃣ 如要查 50 音 → 選『平假名表』再選分類即可查看🎯"
        )
        line_bot_api.reply_message(event.reply_token, TextSendMessage(help_msg))
        return

    # 其他輸入
    line_bot_api.reply_message(event.reply_token, TextSendMessage("輸入『我要練習』或『平假名表』來開始唷 ✍️"))


# ── 啟動伺服器 ─────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
