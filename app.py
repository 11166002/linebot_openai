from flask import Flask, request, jsonify
from collections import deque   # 佇列（給 BFS 用）
import random                   # 隨機數/抽題都會用到
import requests                 # 如果之後要打外部 API

app = Flask(__name__)
# ========== LINE Token ==========
CHANNEL_ACCESS_TOKEN = "liqx01baPcbWbRF5if7oqBsZyf2+2L0eTOwvbIJ6f2Wec6is4sVd5onjl4fQAmc4n8EuqMfo7prlaG5la6kXb/y1gWOnk8ztwjjx2ZnukQbPJQeDwwcPEdFTOGOmQ1t88bQLvgQVczlzc/S9Q/6y5gdB04t89/1O/w1cDnyilFU="

# ========== 📘 日語五十音資料區（kana_dict） ==========
kana_dict = {}

# 清音（基本音）
kana_dict.update({
    "あ": "a", "い": "i", "う": "u", "え": "e", "お": "o",
    "か": "ka", "き": "ki", "く": "ku", "け": "ke", "こ": "ko",
    "さ": "sa", "し": "shi", "す": "su", "せ": "se", "そ": "so",
    "た": "ta", "ち": "chi", "つ": "tsu", "て": "te", "と": "to",
    "な": "na", "に": "ni", "ぬ": "nu", "ね": "ne", "の": "no",
    "は": "ha", "ひ": "hi", "ふ": "fu", "へ": "he", "ほ": "ho",
    "ま": "ma", "み": "mi", "む": "mu", "め": "me", "も": "mo",
    "や": "ya", "ゆ": "yu", "よ": "yo",
    "ら": "ra", "り": "ri", "る": "ru", "れ": "re", "ろ": "ro",
    "わ": "wa", "を": "wo", "ん": "n"
})

# 濁音（有濁點）
kana_dict.update({
    "が": "ga", "ぎ": "gi", "ぐ": "gu", "げ": "ge", "ご": "go",
    "ざ": "za", "じ": "ji", "ず": "zu", "ぜ": "ze", "ぞ": "zo",
    "だ": "da", "ぢ": "ji", "づ": "zu", "で": "de", "ど": "do",
    "ば": "ba", "び": "bi", "ぶ": "bu", "べ": "be", "ぼ": "bo"
})

# 半濁音（有半濁點）
kana_dict.update({
    "ぱ": "pa", "ぴ": "pi", "ぷ": "pu", "ぺ": "pe", "ぽ": "po"
})

# 拗音（拗合音，平假名 + 小字）
kana_dict.update({
    "きゃ": "kya", "きゅ": "kyu", "きょ": "kyo",
    "しゃ": "sha", "しゅ": "shu", "しょ": "sho",
    "ちゃ": "cha", "ちゅ": "chu", "ちょ": "cho",
    "にゃ": "nya", "にゅ": "nyu", "にょ": "nyo",
    "ひゃ": "hya", "ひゅ": "hyu", "ひょ": "hyo",
    "みゃ": "mya", "みゅ": "myu", "みょ": "myo",
    "りゃ": "rya", "りゅ": "ryu", "りょ": "ryo",
    "ぎゃ": "gya", "ぎゅ": "gyu", "ぎょ": "gyo",
    "じゃ": "ja", "じゅ": "ju", "じょ": "jo",
    "びゃ": "bya", "びゅ": "byu", "びょ": "byo",
    "ぴゃ": "pya", "ぴゅ": "pyu", "ぴょ": "pyo"
})

# ========== 回傳純文字訊息 ==========

def reply_text(reply_token, text):
    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text}]
    }
    requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=body)

# ========== 回傳音檔 ==========

def reply_audio(reply_token, original_content_url, duration):
    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "replyToken": reply_token,
        "messages": [{
            "type": "audio",
            "originalContentUrl": original_content_url,
            "duration": duration
        }]
    }
    requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=body)

# ========== 同時回傳文字 + 音檔 ==========

def reply_text_audio(reply_token, text_msg, audio_url, duration):
    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "replyToken": reply_token,
        "messages": [
            {"type": "text", "text": text_msg},
            {"type": "audio", "originalContentUrl": audio_url, "duration": duration}
        ]
    }
    requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=body)

# ========== 音檔清單 ==========
audio_files = [
    "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7).m4a",
    "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7)1.m4a",
    "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7)2.m4a",
    "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7)3.m4a",
    "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7)4.m4a",
    "https://raw.githubusercontent.com/11166002/audio-files/main/%E4%B8%83%E6%B5%B7(%E5%A5%B3%E6%80%A7)5.m4a"
]

# 與音檔對應的假名與羅馬拼音
audio_labels = [
    ("日語：あ", "羅馬拼音：a"),
    ("日語：い", "羅馬拼音：i"),
    ("日語：う", "羅馬拼音：u"),
    ("日語：え", "羅馬拼音：e"),
    ("日語：お", "羅馬拼音：o"),
    ("日語：か", "羅馬拼音：ka")
]

# 🏹 射飛鏢遊戲資料 (含繁體中文意義)
dart_words = {
    "みず": ("mizu", "水"),
    "たべる": ("taberu", "吃"),
    "のむ": ("nomu", "喝"),
    "いく": ("iku", "去"),
    "くるま": ("kuruma", "車"),
    "ともだち": ("tomodachi", "朋友"),
    "せんせい": ("sensei", "老師"),
    "ほん": ("hon", "書"),
    "いぬ": ("inu", "狗"),
    "ねこ": ("neko", "貓")
}

dart_sessions = {}

@app.route("/callback", methods=["POST"])
def callback():
    body = request.get_json()
    events = body.get("events", [])

    for event in events:
        if event["type"] == "message":
            reply_token = event["replyToken"]
            user_id = event["source"]["userId"]
            text = event["message"]["text"].strip()

            if text == "主選單":
                menu = (
                    "請選擇：\n"
                    "1. 我要看五十音\n"
                    "2. 我要聽音檔\n"
                    "3. 我要玩迷宮遊戲\n"
                    "4. 我要玩賽車遊戲\n"
                    "5. 我要玩射飛鏢 進階篇\n"
                    "6. 我要填問卷～\n\n"
                    "【遊戲規則】\n"
                    "📘 看五十音：查看所有平假名、片假名與羅馬拼音對照。\n"
                    "🔊 聽音檔：播放50音發音音檔。\n"
                    "🧩 迷宮遊戲：使用『上/下/左/右』移動角色，遇到假名選擇題時答對才能繼續。\n"
                    "🏎 賽車遊戲：每次輸入『前進』會推進一格，抵達終點即勝利！\n"
                    "🎯 射飛鏢：隨機射中一個日文單字，選出正確的羅馬拼音！"
                )
                reply_text(reply_token, menu)

            elif text == "1" or text == "我要看五十音":
                reply_text(reply_token, get_kana_table())
                
            elif text == "2" or text == "我要聽音檔":
                # 隨機選擇一個音檔並回覆假名 + 音檔（一次回覆）
                idx = random.randrange(len(audio_files))
                kana, roma = audio_labels[idx]
                reply_text_audio(
                    reply_token,
                    f"{kana} ({roma})",          # 文字訊息
                    audio_files[idx],            # 音檔 URL
                    2000                         # 長度 (毫秒)；請依實際音檔長度調整
            )

            elif text == "3" or text == "我要玩迷宮遊戲":
                players[user_id] = {"pos": (1, 1), "quiz": None, "game": "maze", "score": 0}
                reply_text(reply_token, render_map((1, 1)) + "\n🌟 迷宮遊戲開始！請輸入「上」「下」「左」「右」移動。")

            elif text == "4" or text == "我要玩賽車遊戲":
                players[user_id] = {"car_pos": 0, "game": "race", "quiz": None, "last_quiz": None, "last_msg": None}
                reply_text(reply_token, render_race(0) + "\n🏁 賽車遊戲開始！請輸入「前進」來推進你的車子。")

            elif text == "5" or text == "我要玩射飛鏢":
                # --- 先隨機選單字並產生選項、記錄 session ---
                word, (romaji, meaning) = random.choice(list(dart_words.items()))
                options = [romaji]
                while len(options) < 3:
                    distractor = random.choice([v[0] for v in dart_words.values()])
                    if distractor not in options:
                        options.append(distractor)
                random.shuffle(options)
                choice_map = {"A": options[0], "B": options[1], "C": options[2]}
                dart_sessions[user_id] = {
                    "word": word,
                    "meaning": meaning,
                    "answer": romaji,
                    "choice_map": choice_map
                }
                choices_text = "\n".join([f"{k}. {v}" for k, v in choice_map.items()])

                # --- 一次回覆三則訊息：圖片、情境、遊戲題目 ---
                headers = {
                    "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
                    "Content-Type": "application/json"
                }
                body = {
                    "replyToken": reply_token,
                    "messages": [
                        {
                            "type": "image",
                            "originalContentUrl": "https://i.imgur.com/5F3fhhn.png",
                            "previewImageUrl":  "https://i.imgur.com/5F3fhhn.png"
                        },
                        {
                            "type": "text",
                            "text": (
                                "🎯 情境題：你來到熱鬧的日式祭典射飛鏢攤位，"
                                "眼前的靶子上印有日語單字與其中文意義，"
                                "請射中一個單字後，選出其正確的羅馬拼音！"
                            )
                        },
                        {
                            "type": "text",
                            "text": (
                                f"🎯 射飛鏢結果：你射中了「{word}（{meaning}）」！\n"
                                f"請選出正確的羅馬拼音：\n{choices_text}"
                            )
                        }
                    ]
                }
                requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=body)
                # 射飛鏢遊戲開始
                word, (romaji, meaning) = random.choice(list(dart_words.items()))
                options = [romaji]
                while len(options) < 3:
                    distractor = random.choice([v[0] for v in dart_words.values()])
                    if distractor not in options:
                        options.append(distractor)
                random.shuffle(options)
                dart_sessions[user_id] = {"word": word, "meaning": meaning, "answer": romaji, "options": options}
                choice_map = {"A": options[0], "B": options[1], "C": options[2]}
                dart_sessions[user_id]["choice_map"] = choice_map
                choices_text = "\n".join([f"{k}. {v}" for k, v in choice_map.items()])
                reply_text(
                    reply_token,
                    f"🎯 射飛鏢結果：你射中了「{word}（{meaning}）」！\n"
                    f"請選出正確的羅馬拼音：\n{choices_text}"
                )

            elif user_id in dart_sessions and text in ["A", "B", "C"]:
                # 處理射飛鏢答案
                session = dart_sessions[user_id]
                if session["choice_map"][text] == session["answer"]:
                    del dart_sessions[user_id]
                    reply_text(reply_token, "🎯 命中！答對了！")
                else:
                    choices_text = "\n".join([f"{k}. {v}" for k, v in session["choice_map"].items()])
                    reply_text(
                        reply_token,
                        f"❌ 沒射中，再試一次！請選出「{session['word']}（{session['meaning']}）」的正確羅馬拼音：\n{choices_text}"
                    )

            elif text == "6" or text == "我要填問卷～":
                reply_text(reply_token, "📋 請點選以下連結填寫問卷：\nhttps://forms.gle/w5GNDJ7PY9uWTpsG6")

            elif user_id in players and players[user_id].get("game") == "maze" and text in ["上", "下", "左", "右"]:
                result = maze_game(user_id, text)
                reply_text(reply_token, result["map"] + "\n💬 " + result["message"])

            elif user_id in players and players[user_id].get("game") == "maze" and players[user_id].get("quiz"):
                result = maze_game(user_id, text)
                reply_text(reply_token, result["map"] + "\n💬 " + result["message"])

            elif user_id in players and players[user_id].get("game") == "race" and text in ["A", "B", "C", "D"]:
                result = race_answer(user_id, text)
                reply_text(reply_token, result)

            elif user_id in players and players[user_id].get("game") == "race" and text == "前進":
                result = race_game(user_id)
                reply_text(reply_token, result)

            else:
                reply_text(reply_token,
                    "📢 請輸入『主選單』")


def reply_text(reply_token, text):
    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text}]
    }
    requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=body)




# ========== 🧩 迷宮遊戲設定 ==========
import random
from collections import deque
from typing import Set, Tuple, Dict, Any, List, Optional, Union

# --- 基本設定 ---
MAZE_SIZE = 7
START_POS: Tuple[int, int] = (1, 1)
GOAL_POS: Tuple[int, int] = (MAZE_SIZE - 2, MAZE_SIZE - 2)

# --- 地圖元素符號 ---
WALL_SYMBOL = "⬛"
PATH_SYMBOL = "⬜"
PLAYER_SYMBOL = "😊"
GOAL_SYMBOL = "⛩"
HEART_SYMBOL = "💎"
PORTAL_SYMBOL = "🌀"
QUIZ_SYMBOL = "❓" # Optional: Mark quiz spots

# --- 初始地圖結構 ---
# 建立基礎網格和外牆
maze = [[PATH_SYMBOL for _ in range(MAZE_SIZE)] for _ in range(MAZE_SIZE)]
for i in range(MAZE_SIZE):
    maze[0][i] = maze[MAZE_SIZE - 1][i] = WALL_SYMBOL
    maze[i][0] = maze[i][MAZE_SIZE - 1] = WALL_SYMBOL
maze[GOAL_POS[0]][GOAL_POS[1]] = GOAL_SYMBOL

# --- 靜態/初始遊戲元素位置 ---
# (這些會在遊戲重置時恢復)
# 注意：這些是 '潛在' 的牆壁，部分會被 _build_extra_walls 保留
# 確保 start/goal 不在這裡
RAW_POTENTIAL_WALLS: Set[Tuple[int, int]] = {
    (1, 2), (1, 4), (1, 5), # Removed (1,1) as it's start
    (2, 1), (2, 2), (2, 3), (2, 4), (2, 6),
    (3, 1), (3, 3), (3, 5),
    (4, 2), (4, 4), (4, 5), (4, 6), # Removed (4,1) for portal
    (5, 1), (5, 3), (5, 4), (5, 5), # Removed (5,2) for path ensurence
    (6, 2), (6, 3), (6, 4), # Removed (6,5) as it's goal neighbour
}
INIT_HEARTS: Set[Tuple[int, int]] = {(1, 3), (3, 4), (5, 1)} # 💎 (Added one)
INIT_PORTALS: Set[Tuple[int, int]] = {(2, 5), (4, 1)} # 🌀
INIT_QUIZ_POSITIONS: Set[Tuple[int, int]] = {(3, 2), (5, 5)} # 固定的題目觸發點

# --- 假設的假名辭典 (請確保在您的環境中定義了這個) ---
kana_dict: Dict[str, str] = {
    "あ": "a", "い": "i", "う": "u", "え": "e", "お": "o",
    "か": "ka", "き": "ki", "く": "ku", "け": "ke", "こ": "ko",
    "さ": "sa", "し": "shi", "す": "su", "せ": "se", "そ": "so",
    # ... 更多假名
}
if not kana_dict:
    print("警告：`kana_dict` 是空的，測驗功能將無法運作！")


# --- 玩家狀態儲存 ---
# 改用 Type Hinting
PlayerState = Dict[str, Any] # Could be more specific with TypedDict if needed
players: Dict[str, PlayerState] = {}

# ===== 可達性檢查與動態牆壁生成 =====

Pos = Tuple[int, int]

def _is_reachable(blocks: Set[Pos]) -> bool:
    """BFS 檢查在 blocks 為牆的情況下，start 是否仍可達 goal"""
    q, seen = deque([START_POS]), {START_POS}
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    while q:
        y, x = q.popleft()
        if (y, x) == GOAL_POS:
            return True
        for dy, dx in dirs:
            ny, nx = y + dy, x + dx
            pos = (ny, nx)
            if (
                0 <= ny < MAZE_SIZE and 0 <= nx < MAZE_SIZE and
                pos not in blocks and
                maze[ny][nx] != WALL_SYMBOL and # Check against base maze walls
                pos not in seen
            ):
                seen.add(pos)
                q.append(pos)
    return False

def _build_extra_walls(potential_walls: Set[Pos],
                       hearts: Set[Pos],
                       portals: Set[Pos],
                       quiz_spots: Set[Pos]) -> Set[Pos]:
    """產生『保證可達』的可拆牆集合；若仍堵死就返回空集合"""
    # 保護起點、終點及其鄰近格子，以及特殊物品格
    protected = {
        START_POS, GOAL_POS,
        (START_POS[0] + 1, START_POS[1]), (START_POS[0], START_POS[1] + 1),
        (GOAL_POS[0] - 1, GOAL_POS[1]),   (GOAL_POS[0], GOAL_POS[1] - 1),
    } | hearts | portals | quiz_spots

    # 從潛在牆壁中，排除掉被保護的格子
    extra = {wall for wall in potential_walls if wall not in protected}

    # 逐步拆除離終點最遠的牆，直到可達或無牆可拆
    current_blocks = set(extra) # Start with all potential extra walls as blocks
    while current_blocks and not _is_reachable(current_blocks):
        if not current_blocks: break # Should not happen if logic is correct, but safety first
        # 找到離終點曼哈頓距離最遠的牆
        far_wall = max(current_blocks, key=lambda w: abs(w[0] - GOAL_POS[0]) + abs(w[1] - GOAL_POS[1]))
        current_blocks.remove(far_wall) # 'Remove' means it becomes a path

    # 返回確定要當作牆壁的集合
    # 如果最終 current_blocks 使得 start 無法到達 goal，表示初始設定有問題，返回空集合
    if _is_reachable(current_blocks):
         print(f"生成額外牆壁 {len(current_blocks)} 個，迷宮可通行。")
         return current_blocks
    else:
         print(f"警告：無法生成可通行的額外牆壁！迷宮可能無法過關。")
         return set() # Return empty set if goal is unreachable


# ===== 每局可變狀態 =====
# 使用 set() 複製，避免修改到初始設定
heart_positions: Set[Pos] = set(INIT_HEARTS)
portal_positions: Set[Pos] = set(INIT_PORTALS)
quiz_positions: Set[Pos] = set(INIT_QUIZ_POSITIONS)
# 在遊戲開始或重置時才計算 extra_walls
extra_walls: Set[Pos] = _build_extra_walls(RAW_POTENTIAL_WALLS, heart_positions, portal_positions, quiz_positions)


# ===== 輔助函式 =====

def _teleport(pos: Pos, current_portals: Set[Pos]) -> Tuple[Pos, bool]:
    """
    若踩到傳送門且門數 >1，隨機傳送一次。
    返回 (新座標, 是否已傳送)。
    """
    # Cannot teleport if only one portal exists, or not on a portal, or on goal
    if len(current_portals) <= 1 or pos not in current_portals or pos == GOAL_POS:
        return pos, False

    # Choose a destination portal different from the current one
    possible_dests = [p for p in current_portals if p != pos]
    if not possible_dests: # Should not happen if len > 1, but safeguard
         return pos, False
    dest = random.choice(possible_dests)
    print(f"傳送：從 {pos} 到 {dest}")
    return dest, True

def _collect_heart(pos: Pos, player: PlayerState, current_hearts: Set[Pos]) -> bool:
    """踩到寶石就收集並加分；回傳是否真的收集到。會直接修改 current_hearts 集合。"""
    if pos in current_hearts:
        current_hearts.discard(pos) # 安全移除
        player["score"] += 2
        player["items"] += 1
        print(f"玩家 {player.get('id', '未知')} 在 {pos} 撿到寶石")
        return True
    return False

def _generate_quiz(player: PlayerState) -> Optional[Tuple[str, List[Dict[str, str]]]]:
    """
    產生一個假名測驗題目和選項按鈕資料。
    如果 kana_dict 為空，返回 None。
    會直接修改 player 狀態來標記測驗中。
    返回 (題目訊息, 按鈕列表) 或 None。
    """
    if not kana_dict:
        return None

    kana, correct_ans = random.choice(list(kana_dict.items()))
    options = {correct_ans} # Use a set to easily track unique options
    while len(options) < 3:
        distractor = random.choice(list(kana_dict.values()))
        options.add(distractor)

    shuffled_options = list(options)
    random.shuffle(shuffled_options)

    choice_map = {"A": shuffled_options[0], "B": shuffled_options[1], "C": shuffled_options[2]}
    player["quiz"] = {"kana": kana, "answer": correct_ans, "choices": choice_map}
    player["score"] += 1 # 出題加 1 分

    quiz_text = f"❓ 挑戰：「{kana}」的羅馬拼音是？"
    buttons = [
        {'label': f"{k}. {v}", 'action': k} # Label includes the option text
        for k, v in choice_map.items()
    ]
    print(f"向玩家 {player.get('id', '未知')} 出題：{kana} -> {correct_ans}, 選項：{choice_map}")
    return quiz_text, buttons


# ===== 地圖渲染 =====

def render_map(player_pos: Pos, current_hearts: Set[Pos], current_portals: Set[Pos], current_walls: Set[Pos]) -> str:
    """將當前遊戲狀態渲染成地圖字串"""
    rows = []
    for y in range(MAZE_SIZE):
        row_str = ""
        for x in range(MAZE_SIZE):
            cell: Pos = (y, x)
            if cell == player_pos:
                row_str += PLAYER_SYMBOL
            elif cell == GOAL_POS:
                row_str += GOAL_SYMBOL
            elif cell in current_hearts:
                row_str += HEART_SYMBOL
            elif cell in current_portals:
                row_str += PORTAL_SYMBOL
            # elif cell in quiz_positions: # Optionally mark fixed quiz spots
            #     row_str += QUIZ_SYMBOL
            elif maze[y][x] == WALL_SYMBOL or cell in current_walls: # Check base maze and dynamic walls
                row_str += WALL_SYMBOL
            else:
                row_str += PATH_SYMBOL # Assumes PATH_SYMBOL is default empty space
        rows.append(row_str)
    return "\n".join(rows)

# ===== 遊戲主邏輯 =====

# 定義回傳的字典結構，包含可選的按鈕
GameResponse = Dict[str, Union[str, Optional[List[Dict[str, str]]]]]

def maze_game(user_id: str, raw_msg: str) -> GameResponse:
    """
    處理玩家輸入並更新遊戲狀態。
    回傳一個字典包含 'map', 'message', 以及可選的 'buttons'。
    """
    global heart_positions, portal_positions, extra_walls # Allow modification

    # 1. 取得或初始化玩家狀態
    player = players.setdefault(
        user_id,
        {
            "id": user_id, # Store user_id for potential logging
            "pos": START_POS,
            "quiz": None, # Stores {'kana': str, 'answer': str, 'choices': Dict[str, str]}
            "score": 0,
            "items": 0,
            # "game": "maze" # Could be useful if managing multiple games
        },
    )
    current_pos: Pos = player["pos"]
    msg = raw_msg.strip().upper() # Normalize input

    # --- Helper to create response ---
    def create_response(message: str, buttons: Optional[List[Dict[str, str]]] = None) -> GameResponse:
        map_str = render_map(player["pos"], heart_positions, portal_positions, extra_walls)
        response: GameResponse = {"map": map_str, "message": message}
        if buttons:
            response["buttons"] = buttons
        return response

    # 2. 處理測驗回答
    if player["quiz"]:
        quiz_data = player["quiz"]
        kana = quiz_data["kana"]
        correct_ans = quiz_data["answer"]
        choice_map = quiz_data["choices"]

        if msg not in choice_map: # Must answer A, B, or C
            quiz_text = f"❓ 請回答題目：「{kana}」的羅馬拼音是？"
            buttons = [{'label': f"{k}. {v}", 'action': k} for k, v in choice_map.items()]
            return create_response(quiz_text, buttons)

        # Check answer
        is_correct = (choice_map[msg] == correct_ans)
        if is_correct:
            player["quiz"] = None # Clear quiz state
            feedback = "✅ 正確，請繼續前進！"
            return create_response(f"{feedback}\n目前得分：{player['score']} 分")
        else:
            # 錯誤，重新顯示題目和按鈕
            feedback = "❌ 錯誤，再試一次！"
            quiz_text = f"❓ 挑戰：「{kana}」的羅馬拼音是？"
            buttons = [{'label': f"{k}. {v}", 'action': k} for k, v in choice_map.items()]
            return create_response(f"{feedback}\n{quiz_text}", buttons)

    # 3. 處理移動指令
    dir_map: Dict[str, Tuple[int, int]] = {"上": (-1, 0), "下": (1, 0), "左": (0, -1), "右": (0, 1)}
    if msg not in dir_map:
        # 非移動指令，也非測驗回答 (可能需要主選單等)
        if msg == "主選單": # Example handling
             # Reset player or guide them? Depends on desired flow.
             # For now, just remind them how to play.
             return create_response("請輸入方向（上/下/左/右）開始移動。")
        return create_response("請輸入有效指令：上/下/左/右 或 回答題目選項 (A/B/C)。")

    # Calculate potential new position
    dy, dx = dir_map[msg]
    ny, nx = current_pos[0] + dy, current_pos[1] + dx
    next_pos: Pos = (ny, nx)

    # 4. 檢查碰撞 (邊界、基礎牆、動態牆)
    if not (0 <= ny < MAZE_SIZE and 0 <= nx < MAZE_SIZE) or \
       maze[ny][nx] == WALL_SYMBOL or \
       next_pos in extra_walls:
        return create_response("🚧 前方是牆壁或邊界，無法通行！")

    # 5. 更新位置 & 處理格子效果
    player["pos"] = next_pos
    info_messages = [] # Collect messages for this move

    # 5a. 傳送門 (優先處理，因為會改變位置)
    new_pos_after_tp, did_teleport = _teleport(player["pos"], portal_positions)
    if did_teleport:
        player["pos"] = new_pos_after_tp # Update position if teleported
        info_messages.append("🌀 你被傳送門吸入，瞬間移動了！")
        # Re-check hearts/goal at the new teleported position
        current_pos = new_pos_after_tp # Update current_pos for subsequent checks
    else:
        current_pos = next_pos # Update current_pos normally

    # 5b. 撿寶石 (在最終位置檢查)
    if _collect_heart(current_pos, player, heart_positions):
        info_messages.append(f"💎 撿到寶石！得分 +2，目前 {player['score']} 分。")

    # 5c. 抵達終點
    if current_pos == GOAL_POS:
        score, gems = player["score"], player["items"]
        win_message = f"🎉 恭喜抵達終點 {GOAL_SYMBOL}！"
        encouragement = (
            "🌟 你是真正的迷宮大師！" if score >= 10 else
            "👍 表現非常出色！" if score >= 5 else
            "💪 成功過關！繼續努力！"
        )
        final_stats = f"最終得分：{score} 分，收集了 {gems} 個寶石。"
        reset_info = "➡️ 輸入『主選單』或任何指令重新開始。"

        # 清理玩家狀態並重置遊戲元素
        user_id_to_remove = player["id"]
        del players[user_id_to_remove]
        heart_positions = set(INIT_HEARTS)
        portal_positions = set(INIT_PORTALS)
        quiz_positions = set(INIT_QUIZ_POSITIONS)
        extra_walls = _build_extra_walls(RAW_POTENTIAL_WALLS, heart_positions, portal_positions, quiz_positions)
        print(f"玩家 {user_id_to_remove} 到達終點，遊戲重置。")

        # 提供結束訊息和一個返回主選單的按鈕
        win_buttons = [{'label': '主選單', 'action': '主選單'}]
        map_str = render_map(GOAL_POS, heart_positions, portal_positions, extra_walls) # Show final map with goal reached
        full_message = f"{win_message}\n{encouragement}\n{final_stats}\n\n{reset_info}"
        # Include YOU WIN banner in the map string itself for visual flair
        return {"map": map_str + "\n\n      🏆 YOU WIN! 🏆", "message": full_message, "buttons": win_buttons}


    # 5d. 觸發測驗 (固定點或隨機)
    should_quiz = False
    if current_pos in quiz_positions:
        should_quiz = True
        quiz_positions.discard(current_pos) # Fixed spot quiz triggers only once per game
        print(f"玩家 {player['id']} 踩到固定測驗點 {current_pos}")
    elif random.random() < 0.25: # 降低隨機觸發機率 (原 0.4 偏高)
        should_quiz = True
        print(f"玩家 {player['id']} 在 {current_pos} 隨機觸發測驗")

    if should_quiz:
        quiz_result = _generate_quiz(player)
        if quiz_result:
            quiz_text, buttons = quiz_result
            # Combine potential move messages with quiz prompt
            full_message = "\n".join(info_messages) + ("\n" if info_messages else "") + quiz_text
            return create_response(full_message, buttons)
        else:
            info_messages.append("（本想出題，但題庫似乎空了！）") # Handle case where kana_dict is empty

    # 6. 一般移動回覆
    if not info_messages: # If nothing else happened
        info_messages.append("你順利地移動了。")

    # Add score info to the regular move message
    info_messages.append(f"目前得分：{player['score']} 分")
    return create_response("\n".join(info_messages))


# ===== 範例使用 (需要一個能處理按鈕的環境) =====

# print("--- 初始地圖 ---")
# print(render_map(START_POS, heart_positions, portal_positions, extra_walls))
# print("-" * 20)

# # 模擬玩家輸入
# user = "test_player_1"
# response1 = maze_game(user, "右")
# print(f"訊息:\n{response1['message']}")
# print(f"地圖:\n{response1['map']}")
# print(f"按鈕: {response1.get('buttons')}") # 可能為 None
# print("-" * 20)

# response2 = maze_game(user, "下") # 可能觸發測驗
# print(f"訊息:\n{response2['message']}")
# print(f"地圖:\n{response2['map']}")
# print(f"按鈕: {response2.get('buttons')}")
# print("-" * 20)

# # 如果 response2 觸發了測驗，模擬回答
# if response2.get('buttons'):
#      # 假設總是回答 A (可能是錯的)
#      response3 = maze_game(user, "A")
#      print(f"訊息:\n{response3['message']}")
#      print(f"地圖:\n{response3['map']}")
#      print(f"按鈕: {response3.get('buttons')}") # 答錯會再給按鈕
#      print("-" * 20)

#      # 如果答錯了，再答一次 B
#      if response3.get('buttons'):
#          response4 = maze_game(user, "B")
#          print(f"訊息:\n{response4['message']}")
#          print(f"地圖:\n{response4['map']}")
#          print(f"按鈕: {response4.get('buttons')}")
#          print("-" * 20)

# 🏎 強化版賽車遊戲（修正版）
# ------------------------------------------------------------
# 特色（維持不變）：
# ⛽ Fuel、💰 Gold Coins、🚀 Nitro、⭐ Score
# 本次修正：
# 1. 避免 KeyError／NameError：coins 與 nitro 預設值、防止 current_user 未先定義
# 2. player.setdefault 用於兼容舊玩家資料
# 3. coins／nitro 讀取改成 get()，確保安全
# ------------------------------------------------------------

import random

TRACK_LEN = 10        # 賽道長度
COIN_COUNT = 3        # 金幣數量
FUEL_MAX = 3          # 初始油料
NITRO_CHANCE = 0.25   # Nitro 機率

# ⭐ 若主程式尚未宣告，先給預設
try:
    players
except NameError:
    players = {}
try:
    kana_dict
except NameError:
    kana_dict = {}
# 避免 current_user 未定義
current_user = None

# ------------------------------------------------------------

def render_race(pos, kana=None, options=None):
    """賽道與題目畫面 (保持原接口)"""
    track = ["⬜" for _ in range(TRACK_LEN)]
    player = players.get(current_user, {}) if current_user else {}

    # 繪製金幣
    for coin in player.get("coins", set()):
        if 0 <= coin < TRACK_LEN:
            track[coin] = "💰"
    if pos < TRACK_LEN:
        track[pos] = "🏎"

    race_line = "🚗 賽車進度：\n" + "".join(track)
    status = (
        f"\n⛽ Fuel: {player.get('fuel', 0)}  "
        f"⭐ Score: {player.get('score', 0)}  "
        f"🚀 Nitro: {player.get('nitro', 0)}"
    )

    # 終點
    if pos >= TRACK_LEN:
        return (
            "🏁 你贏了！賽車抵達終點！\n"
            f"⭐ 最終得分：{player.get('score', 0)}\n"
            "輸入 '主選單' 重新開始"
        )

    if kana and options:
        options_text = "\n".join([f"{k}. {v}" for k, v in options.items()])
        return (
            f"{race_line}{status}\n\n❓ 請問「{kana}」的羅馬拼音是？\n"
            f"{options_text}\n請按按鈕作答（A/B/C）。"
        )

    return race_line + status


# ------------------------------------------------------------
# 🏎 賽車遊戲回答處理


def race_answer(user, answer):
    player = players.get(user)
    if not player or not player.get("last_quiz"):
        return "沒有待回答的題目，請輸入『前進』以獲得新題目。"

    global current_user
    current_user = user  # 供 render_race 取得玩家資料

    kana, correct, choice_map = player["last_quiz"]

    # ===== 正確答案 =====
    if answer in choice_map and choice_map[answer] == correct:
        step = 1
        nitro_msg = ""
        if random.random() < NITRO_CHANCE:
            extra = random.randint(1, 2)
            step += extra
            player["nitro"] = player.get("nitro", 0) + 1
            nitro_msg = f"🚀 Nitro！額外前進 {extra} 格！"

        player["car_pos"] += step

        # 撿金幣
        if player["car_pos"] in player.get("coins", set()):
            player.setdefault("coins", set()).discard(player["car_pos"])
            player["score"] = player.get("score", 0) + 2
            coin_msg = "💰 撿到金幣 +2 分！"
        else:
            coin_msg = ""

        # 清除題目
        player["quiz"] = None
        player["last_quiz"] = None

        return (
            render_race(player["car_pos"]) +
            f"\n✅ 回答正確！{nitro_msg} {coin_msg}\n請輸入『前進』以獲得新題目！"
        )

    # ===== 錯誤答案 =====
    player["fuel"] = player.get("fuel", FUEL_MAX) - 1
    if player["fuel"] <= 0:
        players.pop(user, None)
        return (
            render_race(player["car_pos"]) +
            "\n🛑 油料耗盡，遊戲結束！輸入 '主選單' 重新開始"
        )

    return (
        render_race(player["car_pos"], kana, choice_map) +
        f"\n❌ 回答錯誤，燃料 -1！剩餘 {player['fuel']} 格，再試一次！"
    )


# ------------------------------------------------------------
# 🏎 賽車遊戲主流程


def race_game(user):
    # 若舊資料缺少新欄位，setdefault 補齊
    player = players.setdefault(user, {})
    player.setdefault("game", "race")
    player.setdefault("car_pos", 0)
    player.setdefault("fuel", FUEL_MAX)
    player.setdefault("score", 0)
    player.setdefault("coins", set(random.sample(range(1, TRACK_LEN - 1), COIN_COUNT)))
    player.setdefault("nitro", 0)

    global current_user
    current_user = user

    # 若已有題目
    if player.get("quiz"):
        kana, correct, choice_map = player["quiz"]
        player["last_quiz"] = (kana, correct, choice_map)
        return render_race(player["car_pos"], kana, choice_map)

    # 產生新題目
    if not kana_dict:
        return "⚠️ kana_dict 尚未初始化，無法出題！"
    kana, correct = random.choice(list(kana_dict.items()))
    options = [correct]
    while len(options) < 3 and len(kana_dict) >= 3:
        distractor = random.choice(list(kana_dict.values()))
        if distractor not in options:
            options.append(distractor)
    # 若題庫不足 3 個選項，填入重複值避免無限迴圈
    while len(options) < 3:
        options.append(correct)
    random.shuffle(options)
    choice_map = {"A": options[0], "B": options[1], "C": options[2]}

    player["quiz"] = (kana, correct, choice_map)
    player["last_quiz"] = (kana, correct, choice_map)

    return render_race(player["car_pos"], kana, choice_map)

# 📘 回傳日語五十音表格式文字
def get_kana_table():
    table = "📘【日語五十音對照表】"
    groups = [
        ("清音 (基本音)", [
            ("あ", "a"), ("い", "i"), ("う", "u"), ("え", "e"), ("お", "o"),
            ("か", "ka"), ("き", "ki"), ("く", "ku"), ("け", "ke"), ("こ", "ko"),
            ("さ", "sa"), ("し", "shi"), ("す", "su"), ("せ", "se"), ("そ", "so"),
            ("た", "ta"), ("ち", "chi"), ("つ", "tsu"), ("て", "te"), ("と", "to"),
            ("な", "na"), ("に", "ni"), ("ぬ", "nu"), ("ね", "ne"), ("の", "no"),
            ("は", "ha"), ("ひ", "hi"), ("ふ", "fu"), ("へ", "he"), ("ほ", "ho"),
            ("ま", "ma"), ("み", "mi"), ("む", "mu"), ("め", "me"), ("も", "mo"),
            ("や", "ya"), ("ゆ", "yu"), ("よ", "yo"),
            ("ら", "ra"), ("り", "ri"), ("る", "ru"), ("れ", "re"), ("ろ", "ro"),
            ("わ", "wa"), ("を", "wo"), ("ん", "n")
        ]),
        ("濁音 (加上濁點)", [
            ("が", "ga"), ("ぎ", "gi"), ("ぐ", "gu"), ("げ", "ge"), ("ご", "go"),
            ("ざ", "za"), ("じ", "ji"), ("ず", "zu"), ("ぜ", "ze"), ("ぞ", "zo"),
            ("だ", "da"), ("ぢ", "ji"), ("づ", "zu"), ("で", "de"), ("ど", "do"),
            ("ば", "ba"), ("び", "bi"), ("ぶ", "bu"), ("べ", "be"), ("ぼ", "bo")
        ]),
        ("半濁音 (加上半濁點)", [
            ("ぱ", "pa"), ("ぴ", "pi"), ("ぷ", "pu"), ("ぺ", "pe"), ("ぽ", "po")
        ]),
        ("拗音 (小字組合音)", [
            ("きゃ", "kya"), ("きゅ", "kyu"), ("きょ", "kyo"),
            ("しゃ", "sha"), ("しゅ", "shu"), ("しょ", "sho"),
            ("ちゃ", "cha"), ("ちゅ", "chu"), ("ちょ", "cho"),
            ("にゃ", "nya"), ("にゅ", "nyu"), ("にょ", "nyo"),
            ("ひゃ", "hya"), ("ひゅ", "hyu"), ("ひょ", "hyo"),
            ("みゃ", "mya"), ("みゅ", "myu"), ("みょ", "myo"),
            ("りゃ", "rya"), ("りゅ", "ryu"), ("りょ", "ryo"),
            ("ぎゃ", "gya"), ("ぎゅ", "gyu"), ("ぎょ", "gyo"),
            ("じゃ", "ja"), ("じゅ", "ju"), ("じょ", "jo"),
            ("びゃ", "bya"), ("びゅ", "byu"), ("びょ", "byo"),
            ("ぴゃ", "pya"), ("ぴゅ", "pyu"), ("ぴょ", "pyo")
        ])
    ]
    for title, kana_group in groups:
        table += f"\n\n🔹 {title}\n"
        for i in range(0, len(kana_group), 5):
            row = kana_group[i:i+5]
            line = "  ".join([f"{kana} → {roma}" for kana, roma in row])
            table += line + "\n"
    return table.strip()
