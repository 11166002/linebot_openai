from flask import Flask, request, jsonify, render_template, abort
import os, base64, cv2, psycopg2, re, random
from urllib.parse import unquote, quote
from skimage.metrics import structural_similarity as ssim
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *

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

# 記憶遊戲狀態（每個使用者一份）
USER_GAME = {}

# =============================
# 工具函式
# =============================

def get_user_id(event) -> str:
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
def fetch_kana_info(kana):
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


def quick_reply_for_row() -> QuickReply:
    """Quick buttons after showing a row (row prev/row next/back to table/help)."""
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="Row ◀",     text="row previous")),
        QuickReplyButton(action=MessageAction(label="Row ▶",     text="row next")),
        QuickReplyButton(action=MessageAction(label="Random",     text="random")),
        QuickReplyButton(action=MessageAction(label="Kana Table", text="Kana Table")),
        QuickReplyButton(action=MessageAction(label="Help",       text="Help")),
    ])


def quick_reply_for_game() -> QuickReply:
    """記憶遊戲的快捷鍵（顯示棋盤/結束/說明）。"""
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="Show Board", text="game show")),
        QuickReplyButton(action=MessageAction(label="End Game",   text="game end")),
        QuickReplyButton(action=MessageAction(label="Game Help",  text="game help")),
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
        TextSendMessage(text=f"""📖 Stroke order description:
{info['stroke_order_text']}"""),
        ImageSendMessage(original_content_url=info['image_url'], preview_image_url=info['image_url']),
        AudioSendMessage(
            original_content_url=info['audio_url'],
            duration=3000,
            quick_reply=quick_reply_for_kana(kana)
        ),
    ]


# =============================
# 記憶遊戲：狀態、棋盤與流程
# =============================

def init_memory_game(uid: str, category: str = "Seion", pairs: int = 5):
    """初始化記憶遊戲（預設 5 對＝10 張卡片；受 LINE Flex 限制建議最多 10）。"""
    # 取得可用的假名清單，限制 pairs 不超過 5 且不超過類別可用數
    available = list(KANA_SEQ.get(category, []))
    pairs = max(2, min(pairs, 5, len(available)//1))
    values = random.sample(available, pairs)
    deck = values + values
    random.shuffle(deck)
    USER_GAME[uid] = {
        "category": category,      # 類別（Seion/Dakuon/Handakuon）
        "deck": deck,              # 牌面值（例如：['あ','そ',...] * 2）
        "matched": [False]*len(deck),
        "revealed": set(),         # 目前翻開但未配對成功的索引
        "pending_hide": set(),     # 上一步配對失敗，下一步前要自動蓋回的索引
        "first_pick": None,        # 第一次翻的索引
        "moves": 0,                # 步數
        "matches": 0,              # 成功配對數
    }


def render_memory_board(uid: str) -> dict:
    """將目前遊戲狀態渲染為 Flex Carousel 棋盤。"""
    state = USER_GAME.get(uid)
    if not state:
        # 沒有遊戲狀態時避免 KeyError，給一個空棋盤提示
        bubble = {
            "type": "bubble",
            "size": "micro",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "No game", "wrap": True}
                ],
            },
        }
        return {"type": "carousel", "contents": [bubble]}
    deck = state["deck"]
    bubbles = []
    for i, val in enumerate(deck):
        is_open = state["matched"][i] or (i in state["revealed"]) or (i in state["pending_hide"]) or (state["first_pick"] == i)
        label = val if is_open else "?"
        bubble = {
            "type": "bubble",
            "size": "micro",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {"type": "message", "label": label, "text": f"flip {i+1}"},
                        "style": "primary",
                        "height": "sm",
                    }
                ],
            },
        }
        bubbles.append(bubble)
    return {"type": "carousel", "contents": bubbles}


def game_status_text(uid: str) -> str:
    """回傳遊戲狀態摘要。"""
    s = USER_GAME.get(uid, {})
    total_pairs = len(s.get("deck", [])) // 2
    return f"Pairs: {s.get('matches',0)}/{total_pairs} | Moves: {s.get('moves',0)}"


from typing import Tuple

def handle_flip(uid: str, index1based: int) -> Tuple[str, bool]:
    """處理翻牌邏輯，回傳（訊息, 是否結束）。"""
    state = USER_GAME.get(uid)
    if not state:
        return "No game in progress. Type 'game start' to begin.", False

    # 若有尚未蓋回的牌，先蓋回（上一輪不相同的配對）
    if state["pending_hide"] and state["first_pick"] is None:
        for idx in list(state["pending_hide"]):
            if idx in state["revealed"]:
                state["revealed"].remove(idx)
        state["pending_hide"].clear()

    deck = state["deck"]
    i = index1based - 1
    if i < 0 or i >= len(deck):
        return f"Invalid card index. Enter 1~{len(deck)}.", False

    if state["matched"][i] or (i in state["revealed"]) or state["first_pick"] == i:
        return "Card already open. Choose another.", False

    # 第一次翻
    if state["first_pick"] is None:
        state["first_pick"] = i
        state["revealed"].add(i)
        return "Flip recorded. Pick another card.", False

    # 第二次翻
    j = i
    a = state["first_pick"]
    state["revealed"].add(j)
    state["moves"] += 1

    if deck[a] == deck[j] and a != j:
        # 配對成功 → 設為 matched 並維持翻開
        state["matched"][a] = True
        state["matched"][j] = True
        state["matches"] += 1
        state["first_pick"] = None
        # 清空 pending_hide（以防萬一）
        state["pending_hide"].clear()
        finished = state["matches"] == (len(deck) // 2)
        if finished:
            return "🎉 Match! You cleared the board!", True
        return "✅ Match! Keep going.", False
    else:
        # 配對失敗 → 暫時顯示兩張，等下一次行動再蓋回
        state["pending_hide"] = {a, j}
        state["first_pick"] = None
        return "❌ Not a match. They will hide on your next action.", False


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
    - Others: 'random' to draw a kana randomly
    - Memory game: 'game start [category] [pairs]', 'flip N', 'game show', 'game end'
    """
    text = event.message.text.strip()
    uid  = get_user_id(event)

    # 入口：Start Practice
    if text == "Start Practice":
        qr = QuickReply(items=[
            QuickReplyButton(action=URIAction(label="Open Canvas", uri=LIFF_URL)),
            QuickReplyButton(action=MessageAction(label="Kana Table", text="Kana Table")),
            QuickReplyButton(action=MessageAction(label="Game", text="game start")),
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

    # Start memory game from Kana Table menu
    if text == "Game":
        if not uid:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("Game requires a user context."))
            return
        cat = USER_STATE.get(uid, {}).get("category", "Seion")
        init_memory_game(uid, cat, 5)
        board = render_memory_board(uid)
        status = game_status_text(uid)
        line_bot_api.reply_message(
            event.reply_token,
            [
                TextSendMessage(text=f"Memory game started. Category: {cat}."),
                FlexSendMessage(alt_text="Memory Game", contents=board),
                TextSendMessage(text=status, quick_reply=quick_reply_for_game()),
            ],
        )
        return

    # 類別選擇
    if text in ("Seion", "Dakuon", "Handakuon"):
        if uid:
            USER_STATE[uid] = {"category": text, "row_index": 0, "last_kana": USER_STATE.get(uid, {}).get("last_kana")}
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text=f"Kana ({text})", contents=kana_flex(text)),
        )
        return

    # 若點了某一整列（字串完全比對）
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

    # 列導覽：row next / row previous
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

        # 更新狀態（類別/列索引/最後假名）
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

    # === 記憶遊戲指令 ===
    # 開始：game start [Seion|Dakuon|Handakuon] [pairs]
    mstart = re.match(r"^game\s+start(?:\s+(Seion|Dakuon|Handakuon))?(?:\s+(\d+))?$", text, flags=re.IGNORECASE)
    if mstart and uid:
        cat = mstart.group(1) or USER_STATE.get(uid, {}).get("category", "Seion")
        pairs = int(mstart.group(2)) if mstart.group(2) else 5
        init_memory_game(uid, cat, pairs)
        board = render_memory_board(uid)
        status = game_status_text(uid)
        line_bot_api.reply_message(
            event.reply_token,
            [
                TextSendMessage(text=f"Memory game started. Category: {cat}."),
                FlexSendMessage(alt_text="Memory Game", contents=board),
                TextSendMessage(text=status, quick_reply=quick_reply_for_game()),
            ],
        )
        return

    # 翻牌：flip N
    mflip = re.match(r"^flip\s+(\d+)$", text, flags=re.IGNORECASE)
    if mflip and uid:
        if uid not in USER_GAME:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("No game in progress. Type 'game start' to begin."))
            return
        n = int(mflip.group(1))
        msg, finished = handle_flip(uid, n)
        board = render_memory_board(uid)
        status = game_status_text(uid)
        msgs = [TextSendMessage(text=msg), FlexSendMessage(alt_text="Memory Game", contents=board), TextSendMessage(text=status, quick_reply=quick_reply_for_game())]
        if finished:
            # 結束 → 自動清掉遊戲狀態
            USER_GAME.pop(uid, None)
            msgs.append(TextSendMessage(text="Game finished! Type 'game start' to play again."))
        line_bot_api.reply_message(event.reply_token, msgs)
        return

    # 顯示棋盤：game show
    if text.lower() == "game show" and uid:
        if uid not in USER_GAME:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("No game in progress. Type 'game start' to begin."))
            return
        # 若有 pending_hide，這次顯示前先蓋回
        state = USER_GAME[uid]
        if state["pending_hide"] and state["first_pick"] is None:
            for idx in list(state["pending_hide"]):
                state["revealed"].discard(idx)
            state["pending_hide"].clear()
        board = render_memory_board(uid)
        status = game_status_text(uid)
        line_bot_api.reply_message(
            event.reply_token,
            [FlexSendMessage(alt_text="Memory Game", contents=board), TextSendMessage(text=status, quick_reply=quick_reply_for_game())],
        )
        return

    # 結束遊戲：game end
    if text.lower() == "game end" and uid:
        if uid in USER_GAME:
            USER_GAME.pop(uid, None)
            line_bot_api.reply_message(event.reply_token, TextSendMessage("Game ended. Type 'game start' to play again."))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("No game in progress."))
        return

    # 遊戲說明：game help
    if text.lower() == "game help":
        ghelp = (
            "🎮 Memory game commands\n"
            "• game start [Seion|Dakuon|Handakuon] [pairs] — start a new game (default 5 pairs).\n"
            "• flip N — flip the Nth card.\n"
            "• game show — show the current board.\n"
            "• game end — quit the current game.\n"
            "Notes: A mismatch stays visible until your next action, then hides automatically.\n"
        )
        line_bot_api.reply_message(event.reply_token, TextSendMessage(ghelp))
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

    # Help（加入遊戲說明）
    if text.lower() == "help":
        help_text = (
            "📘 How to use\n"
            "• Choose a category via 'Kana Table' → Seion/Dakuon/Handakuon.\n"
            "• Pick a row to see kana buttons.\n"
            "• Type commands: next / previous / repeat [kana?], row next / row previous, random.\n"
            "• Memory game: game start [category] [pairs], flip N, game show, game end.\n"
            "• If no kana is given after next/previous/repeat, the last viewed kana will be used.\n"
        )
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
