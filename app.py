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
    """Return a Flex bubble showing kana + romaji (1 行 1 個)."""
    pairs = KANA_CATEGORIES.get(category, [])
    contents = [
        {"type": "text", "text": f"{category} 50 音：每組對應如下👇", "weight": "bold", "size": "lg", "align": "center"}
    ]
    for kana, romaji in pairs:
        contents.append({
            "type": "text",
            "text": f"日文 50 音的假名是『{kana}』，羅馬拼音寫作 {romaji}。",
            "wrap": True,
            "size": "md",
            "margin": "sm"
        })

    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": contents,
        },
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

