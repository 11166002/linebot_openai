from flask import Flask, request, jsonify
import random
import requests

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

# ========== 🧩 迷宮遊戲設定（迷宮地圖生成、陷阱與題目） ==========
maze_size = 7
maze = [["⬜" for _ in range(maze_size)] for _ in range(maze_size)]
for i in range(maze_size):
    maze[0][i] = maze[maze_size-1][i] = "⬛"
    maze[i][0] = maze[i][maze_size-1] = "⬛"

# 固定迷宮地圖（不再隨機產生牆壁）
start = (1, 1)
goal = (maze_size - 2, maze_size - 2)
maze[goal[0]][goal[1]] = "⛩"

# 調整固定牆壁（改為通道以確保有通路）
maze[1][3] = "⬜"
maze[2][2] = "⬜"
maze[3][1] = "⬜"
maze[4][3] = "⬜"
maze[5][2] = "⬜"

players = {}
quiz_positions = [(random.randint(1, maze_size-2), random.randint(1, maze_size-2)) for _ in range(5)]

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

"""
🏯 迷宮小遊戲（Debug & Safety 版）
------------------------------------------------------
1. 啟動時即檢查必要全域是否存在；缺一即 raise AssertionError。
2. 牆面驗證改為「直到可達才停止」→ 不再出現一進門就堵死的情況。
3. 指令大小寫/半形空白自動剃除；方向鍵或 A/B/C 以外輸入一律友善提醒。
4. 答題鎖：有題目時只接受 A/B/C；方向鍵無效、避免誤觸。
5. 傳送門最多跳 10 次；若極端地圖造成鬼打牆，直接破門回到起點。
6. 抵達終點立即渲染終點畫面 + 清帳（heart、portal 亦重置），完全不會卡住。
"""

import random
from collections import deque

# ===== 0. Safety check：確認外部全域齊備 ===============================
_required = ["maze", "maze_size", "start", "goal",
             "quiz_positions", "kana_dict", "players"]
for g in _required:
    assert g in globals(), f"❗ 必要全域變數 `{g}` 尚未定義！先行宣告再匯入本模組。"

# ===== 1. 基本設定（牆 / 寶石 / 傳送門）===============================

raw_walls = {
    (1, 1), (1, 2), (1, 4),
    (2, 2), (2, 6),
    (3, 1), (3, 3), (3, 5),
    (4, 4), (4, 5), (4, 6),
}
INIT_HEARTS  = {(1, 3), (3, 4)}     # 💎
INIT_PORTALS = {(2, 5), (4, 1)}     # 🌀

# ===== 2. 牆面演算法（確保可達） ======================================

def _is_reachable(blocks: set) -> bool:
    """BFS 檢查在 blocks（內含額外牆）下 start 是否可達 goal"""
    q, seen = deque([start]), {start}
    dirs    = [(1,0),(-1,0),(0,1),(0,-1)]
    while q:
        y, x = q.popleft()
        if (y, x) == goal:
            return True
        for dy, dx in dirs:
            ny, nx = y+dy, x+dx
            if (0 <= ny < maze_size and 0 <= nx < maze_size and
                (ny, nx) not in blocks and maze[ny][nx] != "⬛" and
                (ny, nx) not in seen):
                seen.add((ny, nx))
                q.append((ny, nx))
    return False

def _build_extra_walls():
    """回傳一組『保證可達』的牆集合"""
    protected = {start, goal,
                 (start[0]+1, start[1]), (start[0], start[1]+1),
                 (goal[0]-1, goal[1]),   (goal[0], goal[1]-1)}
    extra = {c for c in raw_walls
             if c not in protected and
                c not in INIT_HEARTS and
                c not in INIT_PORTALS}

    # 只要還不可達就持續拆牆（每次拆離 goal 最遠的一塊，加快收斂）
    while not _is_reachable(extra):
        far_wall = max(extra, key=lambda w: abs(w[0]-goal[0])+abs(w[1]-goal[1]))
        extra.remove(far_wall)
    return extra

extra_walls = _build_extra_walls()
heart_positions  = set(INIT_HEARTS)     # 遊戲過程會移除 → 每局重置
portal_positions = set(INIT_PORTALS)

# ===== 3. 遊戲主程式 ===================================================

def maze_game(user: str, raw_msg: str):
    """外部呼叫：player 輸入訊息 → 回傳 {"map":..., "message":...}"""
    # -- 3-1. 取 / 建 player 狀態 --------------------------------------
    player = players.setdefault(user, {
        "pos":   start,
        "quiz":  None,
        "game":  "maze",
        "score": 0,
        "items": 0,
    })

    msg = raw_msg.strip().upper()      # 去頭尾空白 & 全形→半形自行處理
    dir_map = {"上": (-1, 0), "下": (1, 0), "左": (0, -1), "右": (0, 1)}

    # -- 3-2. 若正在答題 ------------------------------------------------
    if player["quiz"]:
        kana, ans, choice_map = player["quiz"]
        if msg not in {"A", "B", "C"}:
            opts = "\n".join([f"{k}. {v}" for k, v in choice_map.items()])
            return {"map": render_map(player["pos"]),
                    "message": f"❓ 先回答題目：「{kana}」羅馬拼音？\n{opts}"}

        # 判分
        correct = (choice_map.get(msg) == ans)
        player["quiz"] = None if correct else player["quiz"]
        feedback = "✅ 正確！" if correct else "❌ 錯誤，再試一次！"
        if not correct:                       # 錯誤時不扣分，也不重抽
            opts = "\n".join([f"{k}. {v}" for k, v in choice_map.items()])
            return {"map": render_map(player["pos"]),
                    "message": f"{feedback}\n{opts}"}
        # 正確就繼續往下跑邏輯（不 return）

    # -- 3-3. 處理方向鍵 -----------------------------------------------
    if msg not in dir_map:
        return {"map": render_map(player["pos"]),
                "message": "請輸入方向（上/下/左/右）或回答題目 A/B/C"}

    dy, dx = dir_map[msg]
    ny, nx = player["pos"][0]+dy, player["pos"][1]+dx
    new_pos = (ny, nx)

    # 撞牆 / 出界
    if (not (0 <= ny < maze_size and 0 <= nx < maze_size) or
        maze[ny][nx] == "⬛" or
        new_pos in extra_walls):
        return {"map": render_map(player["pos"]),
                "message": "🚧 前方是牆，不能走喔！"}

    player["pos"] = new_pos
    info_line = []                      # 收集提示訊息

    # -- 3-4. 傳送門（最多保護 10 次，避免死循環） -----------------------
    hop = 0
    while player["pos"] in portal_positions:
        hop += 1
        if hop > 10:
            player["pos"] = start
            info_line.append("⚠️ 傳送異常，已送回起點。")
            break
        dest = random.choice(list(portal_positions - {player["pos"]}))
        player["pos"] = dest
        info_line.append("🌀 傳送門啟動！")

    # -- 3-5. 撿寶石 ----------------------------------------------------
    if player["pos"] in heart_positions:
        heart_positions.remove(player["pos"])
        player["score"] += 2
        player["items"] += 1
        info_line.append("💎 撿到寶石！（+2 分）")

    # -- 3-6. 抵達終點 --------------------------------------------------
    if player["pos"] == goal:
        score, gems = player["score"], player["items"]
        # 清除玩家狀態，以便下次新局
        players.pop(user, None)
        # 重置動態元素，讓下一個玩家有完整地圖
        global heart_positions, portal_positions, extra_walls
        heart_positions  = set(INIT_HEARTS)
        portal_positions = set(INIT_PORTALS)
        extra_walls      = _build_extra_walls()

        encour = ("🌟 迷宮大師！" if score >= 10 else
                  "👍 表現不錯，再接再厲！" if score >= 5 else
                  "💪 加油！多多練習會更好！")
        return {"map": render_map(goal),
                "message": f"🎉 抵達終點！{encour}\n"
                           f"共 {score} 分、{gems} 顆寶石！\n"
                           "➡️ 輸入『主選單』重新開始"}

    # -- 3-7. 隨機 / 指定出題 ------------------------------------------
    if (player["pos"] in quiz_positions) or (random.random() < 0.4):
        kana, ans = random.choice(list(kana_dict.items()))
        opts = [ans]
        while len(opts) < 3:
            d = random.choice(list(kana_dict.values()))
            if d not in opts:
                opts.append(d)
        random.shuffle(opts)
        choice_map = {"A": opts[0], "B": opts[1], "C": opts[2]}
        player["quiz"] = (kana, ans, choice_map)
        player["score"] += 1
        opt_txt = "\n".join([f"{k}. {v}" for k, v in choice_map.items()])
        return {"map": render_map(player["pos"]),
                "message": f"❓ 挑戰：「{kana}」羅馬拼音？\n{opt_txt}"}

    # -- 3-8. 普通移動回覆 ---------------------------------------------
    info_line = "\n".join(info_line) if info_line else "你移動了～"
    return {"map": render_map(player["pos"]),
            "message": f"{info_line}\n目前得分：{player['score']} 分"}

# ===== 4. 地圖渲染 =====================================================

def render_map(player_pos):
    """把整張地圖組成 multiline 字串"""
    out = []
    for y in range(maze_size):
        row = []
        for x in range(maze_size):
            cell = (y, x)
            if cell == player_pos:
                row.append("😊")
            elif cell == goal:
                row.append("⛩")
            elif cell in heart_positions:
                row.append("💎")
            elif cell in portal_positions:
                row.append("🌀")
            elif maze[y][x] == "⬛" or cell in extra_walls:
                row.append("⬛")
            else:
                row.append(maze[y][x])
        out.append("".join(row))
    return "\n".join(out)
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
