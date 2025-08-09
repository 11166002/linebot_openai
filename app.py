from flask import Flask, request, jsonify, render_template, abort
import os, base64, cv2, psycopg2, re, random, time
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

# 使用者測驗狀態（每位使用者一份）
USER_QUIZ = {}

# =============================
# 工具函式
# =============================

def get_user_id(event) -> Optional[str]:
    """Get LINE user_id; return None if unavailable."""
    return getattr(event.source, "user_id", None)


def safe_url(url: str) -> str:
    """Handle double-encoding and spaces for LINE asset URLs."""
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
                    "image_url": safe_url(row[1]),
                    "stroke_order_text": row[2],
                    "audio_url": safe_url(row[3]),
                }
            return None
    finally:
        conn.close()


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
    """Return the category of a kana; default to 'Seion' if not found."""
    for cat, seq in KANA_SEQ.items():
        if kana in seq:
            return cat
    return "Seion"


def find_row_index_by_kana(cat: str, kana: str) -> int:
    """Return the row index containing the kana within the category; 0 if not found."""
    rows = KANA_ROWS.get(cat, [])
    for idx, row in enumerate(rows):
        if kana in row.split():
            return idx
    return 0


def step_kana(kana: str, step: int = 1) -> str:
    """Within the same category, get the previous/next kana (circular)."""
    cat = category_of(kana)
    seq = KANA_SEQ[cat]
    i = seq.index(kana)
    return seq[(i + step) % len(seq)]


def step_row(cat: str, row_index: int, step: int = 1) -> int:
    """Move to previous/next row within the category (circular)."""
    rows = KANA_ROWS.get(cat, [])
    if not rows:
        return 0
    return (row_index + step) % len(rows)


# =============================
# Quick Reply 建構
# =============================

def quick_reply_for_kana(kana: str) -> QuickReply:
    """Quick buttons when showing kana info (prev/repeat/next/row prev/row next/random)."""
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


def build_quiz_quick_reply(options):
    """建立測驗用 Quick Reply：四個選項 + 50/50 + Repeat + Skip/End/Help。"""
    items = [QuickReplyButton(action=MessageAction(label=o, text=o)) for o in options]
    items.append(QuickReplyButton(action=MessageAction(label="50/50", text="quiz 50")))
    items.append(QuickReplyButton(action=MessageAction(label="Repeat 🔊", text="quiz repeat")))
    items.append(QuickReplyButton(action=MessageAction(label="Skip", text="quiz skip")))
    items.append(QuickReplyButton(action=MessageAction(label="End", text="quiz end")))
    items.append(QuickReplyButton(action=MessageAction(label="Help", text="quiz help")))
    return QuickReply(items=items)


def build_mode_quick_reply() -> QuickReply:
    """建立遊戲模式 Quick Reply（Casual/Timed/Survival）。"""
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="Casual", text="Game Casual")),
        QuickReplyButton(action=MessageAction(label="Timed ⏱", text="Game Timed")),
        QuickReplyButton(action=MessageAction(label="Survival ❤️", text="Game Survival")),
    ])


# =============================
# 訊息建構（假名表）
# =============================

def kana_flex(category: str = "Seion") -> dict:
    """Build the category's row list as a Flex carousel; each row is a button."""
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
    """Build the kana buttons for the selected row (Flex carousel)."""
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
    """Compose messages for kana info (text + image + audio). Attach quick replies on the audio message."""
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
# 快速測驗（音檔 → 選擇題）
# =============================

def init_quiz(uid: str, category: str = "Seion", num_questions: int = 5, mode: str = "casual"):
    """初始化音檔選擇題測驗。"""
    mode = (mode or "casual").lower()
    if mode not in ("casual", "timed", "survival"):
        mode = "casual"
    seq = list(KANA_SEQ.get(category, []))
    n = max(1, min(num_questions, len(seq)))
    questions = random.sample(seq, n)
    USER_QUIZ[uid] = {
        "category": category,
        "questions": questions,
        "index": 0,
        "score": 0,
        "current": None,
        "choices": [],
        "finished": False,
        # 遊戲化
        "mode": mode,            # casual | timed | survival
        "lives": 3 if mode == "survival" else None,
        "time_per_q": 12 if mode == "timed" else None,
        "deadline_ts": None,     # 下一個截止時間（epoch 秒）
        "streak": 0,
        "best_streak": 0,
        "used_5050": False,      # 當前題目是否已用 50/50
    }


def next_quiz_question(uid: str):
    """前進到下一題並產生選項；若已完成則設定 finished。"""
    s = USER_QUIZ.get(uid)
    if not s:
        return None
    if s["index"] >= len(s["questions"]):
        s["finished"] = True
        return None
    target = s["questions"][s["index"]]
    s["current"] = target
    pool = [k for k in KANA_SEQ[s["category"]] if k != target]
    distractors = random.sample(pool, k=min(3, len(pool))) if pool else []
    choices = distractors + [target]
    random.shuffle(choices)
    s["choices"] = choices
    # 計時模式：設定截止時間；重置 50/50 使用狀態
    s["used_5050"] = False
    if s.get("mode") == "timed" and s.get("time_per_q"):
        s["deadline_ts"] = time.time() + int(s["time_per_q"])  # epoch seconds
    else:
        s["deadline_ts"] = None
    return target, choices


def present_quiz_messages(uid: str):
    """產生目前題目的出題訊息（音檔 + 文字 + quick replies）。"""
    s = USER_QUIZ.get(uid)
    if not s or s.get("finished"):
        return [TextSendMessage(text="No quiz in progress. Type 'quiz start' to begin.")]
    idx = s["index"] + 1
    total = len(s["questions"]) if s["questions"] else 0
    target = s.get("current")
    if not target:
        return [TextSendMessage(text="No current question. Type 'quiz start' again.")]
    info = fetch_kana_info(target)
    if not info:
        return [TextSendMessage(text="Quiz data missing. Try 'quiz start' again.")]

    # 狀態列（模式 / 計時 / 生命 / 連擊）
    status_bits = []
    if s.get("mode") == "timed" and s.get("time_per_q"):
        left = max(0, int(s.get("deadline_ts", 0) - time.time())) if s.get("deadline_ts") else s["time_per_q"]
        status_bits.append(f"⏱ {left}s")
    if s.get("mode") == "survival":
        status_bits.append(f"❤️ {s.get('lives', 0)}")
    if s.get("streak", 0) > 1:
        status_bits.append(f"🔥 {s['streak']}")
    status = "  ".join(status_bits)

    return [
        AudioSendMessage(original_content_url=info['audio_url'], duration=3000),
        TextSendMessage(
            text=(f"Q {idx}/{total}: Choose the correct kana" + (f"  |  {status}" if status else "")),
            quick_reply=build_quiz_quick_reply(s["choices"]),
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
    """Compare canvas-uploaded handwriting with the sample using SSIM."""
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
    """Main command handler:
    - Start Practice / Kana Table / Help
    - Category switch: Seion / Dakuon / Handakuon
    - Row navigation: tap row text or 'row next' / 'row previous'
    - Kana navigation: tap kana or 'next/previous/repeat [kana]'
    - Random draw: 'random'
    - Quiz: 'quiz start [mode?] [category?] [N]', 'quiz 50', 'quiz repeat', 'quiz skip', 'quiz end'
    """
    text = event.message.text.strip()
    uid  = get_user_id(event)

    # 入口：Start Practice（不放 Game；Game 放在 Kana Table 選單）
    if text == "Start Practice":
        qr = QuickReply(items=[
            QuickReplyButton(action=URIAction(label="Open Canvas", uri=LIFF_URL)),
            QuickReplyButton(action=MessageAction(label="Kana Table", text="Kana Table")),
            QuickReplyButton(action=MessageAction(label="Help", text="Help")),
        ])
        line_bot_api.reply_message(event.reply_token, TextSendMessage("Choose a function 👇", quick_reply=qr))
        return

    # 入口：Kana Table
    if text == "Kana Table":
        # 預設先記錄類別為 Seion，列索引 0（便於之後 row next/previous）
        if uid:
            USER_STATE[uid] = {"category": "Seion", "row_index": 0, "last_kana": USER_STATE.get(uid, {}).get("last_kana")}
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                "Please choose: Seion / Dakuon / Handakuon",
                quick_reply=QuickReply(items=[
                    QuickReplyButton(action=MessageAction(label="Seion", text="Seion")),
                    QuickReplyButton(action=MessageAction(label="Dakuon", text="Dakuon")),
                    QuickReplyButton(action=MessageAction(label="Handakuon", text="Handakuon")),
                    QuickReplyButton(action=MessageAction(label="Game", text="Game")),
                ]),
            ),
        )
        return

    # Kana Table 下的 Game：先選模式（Casual/Timed/Survival）
    if text == "Game":
        if not uid:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("Quiz requires a user context."))
            return
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage("Choose a mode:", quick_reply=build_mode_quick_reply()),
        )
        return

    # Game 模式選擇後立即開始
    if text in ("Game Casual", "Game Timed", "Game Survival"):
        if not uid:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("Quiz requires a user context."))
            return
        mode = text.split()[-1].lower()  # casual|timed|survival
        cat = USER_STATE.get(uid, {}).get("category", "Seion")
        init_quiz(uid, cat, 5, mode)
        next_quiz_question(uid)
        msgs = present_quiz_messages(uid)
        line_bot_api.reply_message(event.reply_token, msgs)
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

    # === 測驗指令 ===
    # quiz start [mode?] [Seion|Dakuon|Handakuon]? [N]?
    m_qstart = re.match(r"^quiz\s+start(?:\s+(casual|timed|survival))?(?:\s+(Seion|Dakuon|Handakuon))?(?:\s+(\d+))?$", text, flags=re.IGNORECASE)
    if m_qstart and uid:
        mode = (m_qstart.group(1) or "casual").lower()
        cat = m_qstart.group(2) or USER_STATE.get(uid, {}).get("category", "Seion")
        num = int(m_qstart.group(3)) if m_qstart.group(3) else 5
        init_quiz(uid, cat, num, mode)
        next_quiz_question(uid)
        msgs = present_quiz_messages(uid)
        line_bot_api.reply_message(event.reply_token, msgs)
        return

    # quiz 50（當前題目 50/50）
    if text.lower() in ("quiz 50", "quiz fifty") and uid:
        s = USER_QUIZ.get(uid)
        if not s or s.get("finished") or not s.get("current"):
            line_bot_api.reply_message(event.reply_token, TextSendMessage("No quiz in progress."))
            return
        if s.get("used_5050"):
            line_bot_api.reply_message(event.reply_token, TextSendMessage("50/50 already used on this question."))
            return
        correct = s["current"]
        wrongs = [c for c in s["choices"] if c != correct]
        while len(s["choices"]) > 2 and wrongs:
            removed = wrongs.pop()
            if removed in s["choices"] and removed != correct:
                s["choices"].remove(removed)
        s["used_5050"] = True
        msgs = present_quiz_messages(uid)
        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text="50/50 applied."), *msgs])
        return

    # quiz repeat（重播音檔）
    if text.lower() == "quiz repeat" and uid:
        s = USER_QUIZ.get(uid)
        if not s or s.get("finished") or not s.get("current"):
            line_bot_api.reply_message(event.reply_token, TextSendMessage("No quiz in progress."))
            return
        info = fetch_kana_info(s["current"])
        if not info:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("Audio unavailable."))
            return
        line_bot_api.reply_message(event.reply_token, [AudioSendMessage(original_content_url=info['audio_url'], duration=3000)])
        return

    # quiz skip
    if text.lower() == "quiz skip" and uid:
        s = USER_QUIZ.get(uid)
        if not s or s.get("finished"):
            line_bot_api.reply_message(event.reply_token, TextSendMessage("No quiz in progress."))
            return
        correct = s.get("current")
        # Survival 模式跳題扣命
        if s.get("mode") == "survival" and s.get("lives") is not None:
            s["lives"] -= 1
        s["streak"] = 0
        s["index"] += 1
        next_quiz_question(uid)
        if s.get("mode") == "survival" and s.get("lives") is not None and s["lives"] <= 0:
            total = len(s.get("questions", []))
            score = s.get("score", 0)
            USER_QUIZ.pop(uid, None)
            line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=f"Skipped. Answer: {correct}"), TextSendMessage(text=f"Game over! Score: {score}/{total}")])
            return
        msgs = [TextSendMessage(text=f"Skipped. Answer: {correct}")]
        msgs += present_quiz_messages(uid)
        line_bot_api.reply_message(event.reply_token, msgs)
        return

    # quiz end
    if text.lower() == "quiz end" and uid:
        s = USER_QUIZ.pop(uid, None)
        if not s:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("No quiz in progress."))
            return
        total = len(s.get("questions", []))
        score = s.get("score", 0)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"Quiz ended. Score: {score}/{total}"))
        return

    # quiz help
    if text.lower() == "quiz help":
        msg = (
            "🎯 Kana Quiz (audio → choices)\n"
            "Modes: casual (score), timed (time limit), survival (3 lives).\n"
            "Commands:\n"
            "• quiz start [casual|timed|survival] [Seion|Dakuon|Handakuon] [N]\n"
            "• quiz 50 — remove two wrong options.\n"
            "• quiz repeat — replay the audio.\n"
            "• quiz skip — skip current question.\n"
            "• quiz end — end the quiz.\n"
            "Answer by tapping one of the kana options."
        )
        line_bot_api.reply_message(event.reply_token, TextSendMessage(msg))
        return

    # === 測驗作答攔截（在一般假名邏輯之前）===
    if uid and uid in USER_QUIZ:
        s = USER_QUIZ.get(uid)
        if s and not s.get("finished") and s.get("current") and s.get("choices"):
            # 計時模式：超時直接判錯並進下一題
            if s.get("mode") == "timed" and s.get("deadline_ts"):
                if time.time() > s["deadline_ts"]:
                    correct = s["current"]
                    s["streak"] = 0
                    s["index"] += 1
                    next_quiz_question(uid)
                    if s.get("finished"):
                        total = len(s.get("questions", []))
                        score = s.get("score", 0)
                        USER_QUIZ.pop(uid, None)
                        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text="⏱ Time's up!"), TextSendMessage(text=f"Done! Score: {score}/{total}")])
                    else:
                        msgs = [TextSendMessage(text="⏱ Time's up!")]
                        msgs += present_quiz_messages(uid)
                        line_bot_api.reply_message(event.reply_token, msgs)
                    return
            # 作答
            if text in s["choices"]:
                correct = s["current"]
                if text == correct:
                    s["score"] += 1
                    s["streak"] += 1
                    s["best_streak"] = max(s["best_streak"], s["streak"])
                    feedback = "✅ Correct!" + (f" 🔥 x{s['streak']}" if s['streak'] > 1 else "")
                else:
                    # Survival 模式扣命
                    if s.get("mode") == "survival" and s.get("lives") is not None:
                        s["lives"] -= 1
                    s["streak"] = 0
                    feedback = f"❌ Incorrect. Answer: {correct}"
                s["index"] += 1
                next_quiz_question(uid)
                # Survival 死亡
                if s.get("mode") == "survival" and s.get("lives") is not None and s["lives"] <= 0:
                    total = len(s.get("questions", []))
                    score = s.get("score", 0)
                    USER_QUIZ.pop(uid, None)
                    line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=feedback), TextSendMessage(text=f"Game over! Score: {score}/{total}")])
                    return
                if s.get("finished"):
                    total = len(s.get("questions", []))
                    score = s.get("score", 0)
                    USER_QUIZ.pop(uid, None)
                    line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=feedback), TextSendMessage(text=f"Done! Score: {score}/{total}")])
                else:
                    msgs = [TextSendMessage(text=feedback)]
                    msgs += present_quiz_messages(uid)
                    line_bot_api.reply_message(event.reply_token, msgs)
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

    # Help（加入測驗說明）
    if text.lower() == "help":
        help_text = """📘 How to use
• Choose a category via 'Kana Table' → Seion/Dakuon/Handakuon.
• Pick a row to see kana buttons.
• Commands: next / previous / repeat [kana?], row next / row previous, random.
• Game in 'Kana Table' → choose mode (Casual / Timed / Survival).
• Quiz: quiz start [mode?] [category?] [N], quiz 50, quiz repeat, quiz skip, quiz end.
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
