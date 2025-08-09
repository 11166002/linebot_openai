from flask import Flask, request, jsonify, render_template, abort
import os, base64, cv2, psycopg2, re, random
from urllib.parse import unquote, quote
from skimage.metrics import structural_similarity as ssim
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
from typing import Optional

# ── 🔑 Required (production 建議用環境變數) ──
LINE_CHANNEL_ACCESS_TOKEN = "liqx01baPcbWbRF5if7oqBsZyf2+2L0eTOwvbIJ6f2Wec6is4sVd5onjl4fQAmc4n8EuqMfo7prlaG5la6kXb/y1gWOnk8ztwjjx2ZnukQbPJQeDwwcPEdFTOGOmQ1t88bQLvgQVczlzc/S9Q/6y5gdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET       = "cd9fbd2ce22b12f243c5fcd2d97e5680"
LIFF_URL                  = "https://liff.line.me/2007396139-Q0E29b2o"
# ─────────────────────────────────────────

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static")
SAMPLE_FOLDER = os.path.join(BASE_DIR, "samples")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SAMPLE_FOLDER, exist_ok=True)

# =============================
# 假名表（單一來源）
# =============================
KANA_ROWS = {
    "Seion": [
        "あ い う え お", "か き く け こ", "さ し す せ そ",
        "た ち つ て と", "な に ぬ ね の", "は ひ ふ へ ほ",
        "ま み む め も", "や ゆ よ", "ら り る れ ろ", "わ を ん",
    ],
    "Dakuon": [
        "が ぎ ぐ げ ご", "ざ じ ず ぜ ぞ", "だ ぢ づ で ど", "ば び ぶ べ ぼ",
    ],
    "Handakuon": [
        "ぱ ぴ ぷ ぺ ぽ",
    ],
}

# 將每個類別攤平成序列，用於上一個/下一個定位
KANA_SEQ = {cat: [kana for row in rows for kana in row.split()] for cat, rows in KANA_ROWS.items()}
ALL_KANA = set(k for seq in KANA_SEQ.values() for k in seq)

# 使用者狀態（記錄最後一次的假名/分類/列索引）
USER_STATE = {}

# =============================
# 工具函式
# =============================

def get_user_id(event) -> Optional[str]:
    """取得 LINE user_id；若無法取得則回傳 None。"""
    return getattr(event.source, "user_id", None)


def safe_url(url: str) -> str:
    """處理雙重編碼與空白，確保 LINE 可正確下載資源。"""
    return quote(unquote(url), safe=":/?=&")


# ✅ PostgreSQL 連線（Render 範例）
def get_db_connection():
    # Render 通常需要 SSL，加入 sslmode='require' 以避免連線被拒
    return psycopg2.connect(
        host="dpg-d29lgk2dbo4c73bmamsg-a.oregon-postgres.render.com",
        port="5432",
        database="japan_2tmc",
        user="japan_2tmc_user",
        password="wjEjoFXbdPA8WYTJTkg0mI5oR02ozdnI",
        sslmode="require",
        connect_timeout=10,
    )


# ✅ 由資料庫撈取假名資訊
def fetch_kana_info(kana: str):
    # 連線失敗時避免整個流程炸掉，直接回 None
    try:
        conn = get_db_connection()
    except Exception:
        return None
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT kana, image_url, stroke_order_text, audio_url FROM kana_items WHERE kana = %s",
                (kana,),
            )
            row = cursor.fetchone()
            if row:
                return {
                    "kana": row[0],
                    "image_url": safe_url(row[1] or ""),
                    "stroke_order_text": row[2] or "",
                    "audio_url": safe_url(row[3] or ""),
                }
            return None
    finally:
        try:
            conn.close()
        except Exception:
            pass


# ✅ 影像相似度（SSIM）
def compare_images(user_img_path: str, correct_img_path: str) -> float:
    img1 = cv2.imread(user_img_path, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(correct_img_path, cv2.IMREAD_GRAYSCALE)
    if img1 is None or img2 is None:
        raise FileNotFoundError("❌ Unable to load image (user or sample)")
    img1, img2 = [cv2.resize(i, (200, 200)) for i in (img1, img2)]
    score, _ = ssim(img1, img2, full=True)
    return score


# =============================
# 類別/列/索引定位
# =============================

def category_of(kana: str) -> str:
    """回傳該假名所屬類別；找不到則預設為 'Seion'。"""
    for cat, seq in KANA_SEQ.items():
        if kana in seq:
            return cat
    return "Seion"


def find_row_index_by_kana(cat: str, kana: str) -> int:
    """在給定類別中找出包含此假名的列索引；找不到回傳 0。"""
    rows = KANA_ROWS.get(cat, [])
    for idx, row in enumerate(rows):
        if kana in row.split():
            return idx
    return 0


def step_kana(kana: str, step: int = 1) -> str:
    """在同一類別內取得前/後一個假名（循環）。"""
    cat = category_of(kana)
    seq = KANA_SEQ[cat]
    i = seq.index(kana)
    return seq[(i + step) % len(seq)]


def step_row(cat: str, row_index: int, step: int = 1) -> int:
    """在類別內移動至上一列/下一列（循環）。"""
    rows = KANA_ROWS.get(cat, [])
    if not rows:
        return 0
    return (row_index + step) % len(rows)


# =============================
# Quick Reply 建構
# =============================

def quick_reply_for_kana(kana: str) -> QuickReply:
    """顯示單一假名資訊時的快捷按鈕（上一個/重播/下一個/列前/列後/隨機/返回）。"""
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="◀ Previous", text=f"previous {kana}")),
        QuickReplyButton(action=MessageAction(label="🔁 Repeat",   text=f"repeat {kana}")),
        QuickReplyButton(action=MessageAction(label="Next ▶",     text=f"next {kana}")),
        QuickReplyButton(action=MessageAction(label="Row ◀",      text="row previous")),
        QuickReplyButton(action=MessageAction(label="Row ▶",      text="row next")),
        QuickReplyButton(action=MessageAction(label="Random",      text="random")),
        QuickReplyButton(action=MessageAction(label="Kana Table",  text="Kana Table")),
        QuickReplyButton(action=MessageAction(label="Help",        text="Help")),
    ])


# =============================
# 訊息建構（假名表）
# =============================

def kana_flex(category: str = "Seion") -> dict:
    """以 Flex Carousel 呈現該類別的每一列；每列為一個按鈕。"""
    rows = KANA_ROWS.get(category, [])
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
                        "action": {"type": "message", "label": row.strip(), "text": row.strip()},
                        "style": "primary",
                        "height": "sm",
                    }
                ],
            },
        }
        bubbles.append(bubble)
    return {"type": "carousel", "contents": bubbles}


def generate_kana_buttons(row: str) -> dict:
    """針對所選的一整列，產生該列中每個假名的按鈕（Flex Carousel）。"""
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
                        "action": {"type": "message", "label": kana, "text": kana},
                        "style": "primary",
                        "height": "sm",
                    }
                ],
            },
        }
        bubbles.append(bubble)
    return {"type": "carousel", "contents": bubbles}


def kana_info_messages(kana: str):
    """組合單一假名的資訊（文字＋圖片＋音檔）；導航快捷鍵綁在音檔訊息上。"""
    info = fetch_kana_info(kana)
    if not info:
        return None
    return [
        TextSendMessage(text=f"📖 Stroke order description:\n{info['stroke_order_text']}"),
        ImageSendMessage(original_content_url=info['image_url'], preview_image_url=info['image_url']),
        AudioSendMessage(
            original_content_url=info['audio_url'],
            duration=3000,
            quick_reply=quick_reply_for_kana(kana),
        ),
    ]


# =============================
# LINE Bot 初始化與路由
# =============================
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler      = WebhookHandler(LINE_CHANNEL_SECRET)


@app.route("/")
def home():
    # 若沒有 templates/index.html，回傳簡單訊息避免 TemplateNotFound
    index_path = os.path.join(BASE_DIR, "templates", "index.html")
    if os.path.exists(index_path):
        return render_template("index.html")
    return "OK"


@app.route("/check", methods=["POST"])
def check_image():
    """比較使用者手寫圖與範例圖的相似度（SSIM）。"""
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
            "message": "✅ Correct! Great job!" if score > 0.6 else "❌ Try again!",
        })
    except Exception as e:
        return jsonify({"correct": False, "error": str(e)}), 500


@handler.add(MessageEvent, message=TextMessage)
def handle_msg(event):
    """主要指令處理：
    - Start Practice / Kana Table / Help
    - 類別切換：Seion / Dakuon / Handakuon
    - 列導覽：點整列文字或輸入 'row next' / 'row previous'
    - 假名導覽：點假名或輸入 'next/previous/repeat [kana]'
    - 隨機抽題：'random'
    """
    text = event.message.text.strip()
    uid  = get_user_id(event)

    # 入口：Start Practice（不放 Game）
    if text == "Start Practice":
        qr = QuickReply(items=[
            QuickReplyButton(action=URIAction(label="Open Canvas", uri=LIFF_URL)),
            QuickReplyButton(action=MessageAction(label="Kana Table", text="Kana Table")),
            QuickReplyButton(action=MessageAction(label="Help", text="Help")),
        ])
        line_bot_api.reply_message(event.reply_token, TextSendMessage("Choose a function 👇", quick_reply=qr))
        return

    # 入口：Kana Table（改為按鈕樣板 ButtonsTemplate）
    if text == "Kana Table":
        # 預設先記錄類別為 Seion，列索引 0（便於之後 row next/previous）
        if uid:
            USER_STATE[uid] = {"category": "Seion", "row_index": 0, "last_kana": USER_STATE.get(uid, {}).get("last_kana")}
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(
                alt_text="Select a category",
                template=ButtonsTemplate(
                    title="Kana Table",
                    text="Please choose a category",
                    actions=[
                        MessageAction(label="Seion", text="Seion"),
                        MessageAction(label="Dakuon", text="Dakuon"),
                        MessageAction(label="Handakuon", text="Handakuon"),
                    ],
                ),
            ),
        )
        return

    # 類別選擇 → 顯示列清單（無 quick replies）
    if text in ("Seion", "Dakuon", "Handakuon"):
        if uid:
            USER_STATE[uid] = {"category": text, "row_index": 0, "last_kana": USER_STATE.get(uid, {}).get("last_kana")}
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text=f"Kana ({text})", contents=kana_flex(text)),
        )
        return

    # 若點了某一整列（字串完全比對） → 顯示該列假名按鈕（無 quick replies）
    if text in [*KANA_ROWS["Seion"], *KANA_ROWS["Dakuon"], *KANA_ROWS["Handakuon"]]:
        for cat, rows in KANA_ROWS.items():
            if text in rows:
                row_idx = rows.index(text)
                if uid:
                    state = USER_STATE.get(uid, {})
                    state.update({"category": cat, "row_index": row_idx})
                    USER_STATE[uid] = state
                break
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text="Select a kana", contents=generate_kana_buttons(text)),
        )
        return

    # 列導覽：row next / row previous（仍不加 quick replies）
    mrow = re.match(r"^row\s+(next|previous)$", text, flags=re.IGNORECASE)
    if mrow:
        direction = mrow.group(1).lower()
        state = USER_STATE.get(uid, {"category": "Seion", "row_index": 0}) if uid else {"category": "Seion", "row_index": 0}
        cat = state.get("category", "Seion")
        row_index = state.get("row_index", 0)
        row_index = step_row(cat, row_index, +1 if direction == "next" else -1)
        if uid:
            state.update({"row_index": row_index})
            USER_STATE[uid] = state
        row_text = KANA_ROWS[cat][row_index]
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text=f"{cat} row", contents=generate_kana_buttons(row_text)),
        )
        return

    # 假名導覽：next / previous / repeat [kana?]
    mnav = re.match(r"^(next|previous|repeat)(?:\s+(.+))?$", text, flags=re.IGNORECASE)
    if mnav:
        action, maybe_kana = mnav.group(1).lower(), (mnav.group(2) or "").strip()
        state = USER_STATE.get(uid, {}) if uid else {}
        current = None
        if maybe_kana in ALL_KANA:
            current = maybe_kana
        elif state.get("last_kana") in ALL_KANA:
            current = state["last_kana"]

        if not current:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage("Please select a kana first, or add a kana after the command, e.g., 'next あ'."),
            )
            return

        if action == "repeat":
            target = current
        elif action == "next":
            target = step_kana(current, +1)
        else:
            target = step_kana(current, -1)

        cat = category_of(target)
        row_idx = find_row_index_by_kana(cat, target)
        if uid:
            USER_STATE[uid] = {"category": cat, "row_index": row_idx, "last_kana": target}

        messages = kana_info_messages(target)
        if messages:
            line_bot_api.reply_message(event.reply_token, messages)
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("❌ Data for the kana could not be found."))
        return

    # 隨機抽一個假名（依目前類別；若無狀態則預設 Seion）
    if text.lower() == "random":
        state = USER_STATE.get(uid, {"category": "Seion"}) if uid else {"category": "Seion"}
        cat = state.get("category", "Seion")
        target = random.choice(KANA_SEQ[cat])
        row_idx = find_row_index_by_kana(cat, target)
        if uid:
            USER_STATE[uid] = {"category": cat, "row_index": row_idx, "last_kana": target}
        messages = kana_info_messages(target)
        if messages:
            line_bot_api.reply_message(event.reply_token, messages)
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("❌ Data for the kana could not be found."))
        return

    # 單一假名（直接點選）
    if text in ALL_KANA:
        cat = category_of(text)
        row_idx = find_row_index_by_kana(cat, text)
        if uid:
            USER_STATE[uid] = {"category": cat, "row_index": row_idx, "last_kana": text}
        messages = kana_info_messages(text)
        if messages:
            line_bot_api.reply_message(event.reply_token, messages)
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("❌ Data for the kana could not be found."))
        return

    # Help（移除遊戲說明）
    if text.lower() == "help":
        help_text = """📘 How to use
• Choose a category via 'Kana Table' → Seion/Dakuon/Handakuon.
• Pick a row to see kana buttons.
• Commands: next / previous / repeat [kana?], row next / row previous, random.
• If no kana is given after next/previous/repeat, the last viewed kana will be used.
"""
        line_bot_api.reply_message(event.reply_token, TextSendMessage(help_text))
        return

    # 其他：提示從 Start Practice 開始
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
