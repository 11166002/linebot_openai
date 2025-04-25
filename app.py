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

# 🧩 迷宮遊戲邏輯

# 額外趣味元素：寶石與傳送門
# -------------------------------------------------
# 💎  heart_positions: 玩家踩到會加分並從地圖上移除
# 🌀  portal_positions: 玩家踩到會隨機傳送到另一個傳送門
# -------------------------------------------------

heart_positions = {(1, 3), (3, 4)}   # 可以自行增加座標
portal_positions = {(2, 5), (4, 1)}   # 必須成對存在


def maze_game(user, message):
    player = players.setdefault(
        user,
        {
            "pos": start,
            "quiz": None,
            "game": "maze",
            "score": 0,
            "items": 0,  # 收集的寶石數
        },
    )

    # 有待回答題目：處理答案（答案為 A/B/C）
    if player.get("quiz"):
        kana, answer, choice_map = player["quiz"]
        if message in choice_map and choice_map[message] == answer:
            player["quiz"] = None
            return {
                "map": render_map(player["pos"]),
                "message": "✅ 回答正確，繼續前進！",
            }
        else:
            options_text = "\n".join([f"{key}. {val}" for key, val in choice_map.items()])
            return {
                "map": render_map(player["pos"]),
                "message": f"❌ 回答錯誤，請再試一次：\n{options_text}",
            }

    # 處理移動指令
    direction = {
        "上": (-1, 0),
        "下": (1, 0),
        "左": (0, -1),
        "右": (0, 1),
    }
    if message not in direction:
        return {
            "map": render_map(player["pos"]),
            "message": "請輸入方向：上、下、左、右",
        }

    dy, dx = direction[message]
    y, x = player["pos"]
    new_pos = (y + dy, x + dx)

    # 撞牆
    if not (
        0 <= new_pos[0] < maze_size and 0 <= new_pos[1] < maze_size
    ) or maze[new_pos[0]][new_pos[1]] == "⬛":
        return {
            "map": render_map(player["pos"]),
            "message": "🚧 前方是牆，不能走喔！",
        }

    player["pos"] = new_pos
    bonus_msg = ""  # 走到特殊格子的提示

    # 觸發傳送門
    if new_pos in portal_positions:
        # 將玩家瞬移到另一個傳送門（若有多個隨機挑一）
        other_portals = list(portal_positions - {new_pos})
        if other_portals:
            player["pos"] = random.choice(other_portals)
            new_pos = player["pos"]
            bonus_msg += "🌀 你進入傳送門，被傳送到另一處！\n"

    # 撿到寶石
    if new_pos in heart_positions:
        heart_positions.remove(new_pos)
        player["score"] += 2
        player["items"] += 1
        bonus_msg += "💎 你撿到寶石！（+2 分）\n"

    # 到達終點
    if new_pos == goal:
        final_score = player.get("score", 0)
        gems = player.get("items", 0)
        players.pop(user)
        return {
            "map": render_map(new_pos),
            "message": f"🎉 恭喜你到達終點！共獲得 {final_score} 分、{gems} 顆寶石！輸入 '主選單' 重新開始",
        }

    # 進入出題格或隨機出題
    if new_pos in quiz_positions or random.random() < 0.4:
        kana, correct = random.choice(list(kana_dict.items()))
        options = [correct]
        while len(options) < 3:
            distractor = random.choice(list(kana_dict.values()))
            if distractor not in options:
                options.append(distractor)
        random.shuffle(options)
        choice_map = {"A": options[0], "B": options[1], "C": options[2]}
        player["quiz"] = (kana, correct, choice_map)
        player["score"] += 1
        options_text = "\n".join([f"{key}. {val}" for key, val in choice_map.items()])
        return {
            "map": render_map(new_pos),
            "message": f"❓ 挑戰：「{kana}」的羅馬拼音是？\n請從下列選項點選：\n{options_text}",
        }

    # 一般移動回覆
    return {
        "map": render_map(new_pos),
        "message": f"{bonus_msg}你移動了，可以繼續前進（得分 {player.get('score', 0)} 分）",
    }


# 🧩 顯示迷宮地圖

def render_map(player_pos):
    result = ""
    for y in range(maze_size):
        for x in range(maze_size):
            if (y, x) == player_pos:
                result += "😊"  # 玩家位置
            elif (y, x) == goal:
                result += "⛩"  # 終點
            elif (y, x) in heart_positions:
                result += "💎"  # 未被撿起的寶石
            elif (y, x) in portal_positions:
                result += "🌀"  # 傳送門
            else:
                result += maze[y][x]
        result += "\n"
    return result.strip()


# 🏎 賽車遊戲（強化版）

# 額外趣味元素：
# -------------------------------------------------
# 💰  coin_positions: 撿到可加分並從賽道移除
# ⚡  nitro_chance: 正確作答後有機會觸發 Nitro，額外前進 1~2 格
# ⛽  fuel: 錯誤回答會消耗 1 點燃料；燃料歸零則遊戲失敗
# -------------------------------------------------

track_length = 10
nitro_chance = 0.25  # 25% 機率觸發 Nitro


def render_race(pos, kana=None, options=None):
    """顯示賽道、題目與油量/分數"""
    player = current_player  # 在呼叫端設定 global 供顯示用
    track = ["⬜" for _ in range(track_length)]
    # 動態顯示賽道物件
    for coin in player.get("coins", set()):
        if 0 <= coin < track_length:
            track[coin] = "💰"
    track[min(pos, track_length - 1)] = "🏎"

    race_line = "🚗 賽車進度：\n" + "".join(track)
    status = f"\n🔥 Nitro: {player.get('nitro', 0)}  |  ⛽ Fuel: {player.get('fuel', 3)}  |  ⭐ Score: {player.get('score', 0)}"

    if pos >= track_length:
        return (
            "🏁 你贏了！賽車抵達終點！\n"
            f"⭐ 最終得分：{player.get('score', 0)}\n"
            "輸入 '主選單' 重新開始"
        )

    if kana and options:
        options_text = "\n".join([f"{key}. {val}" for key, val in options.items()])
        return (
            f"{race_line}{status}\n\n❓ 請問「{kana}」的羅馬拼音是？\n{options_text}\n請按按鈕作答（A/B/C）。"
        )
    return race_line + status


# 🏎 賽車遊戲回答處理

def race_answer(user, answer):
    player = players.get(user)
    if not player or not player.get("last_quiz"):
        return "沒有待回答的題目，請輸入『前進』以獲得新題目。"

    kana, correct, choice_map = player["last_quiz"]

    global current_player
    current_player = player  # 供 render_race 使用

    if answer in choice_map and choice_map[answer] == correct:
        # 正確：計算 Nitro 與進度
        step = 1
        if random.random() < nitro_chance:
            extra = random.randint(1, 2)
            step += extra
            player["nitro"] = player.get("nitro", 0) + 1
            nitro_msg = f"🚀 Nitro！額外前進 {extra} 格！"
        else:
            nitro_msg = ""

        player["car_pos"] += step
        # 撿到寶石（💰）
        if player["car_pos"] in player.get("coins", set()):
            player["coins"].remove(player["car_pos"])
            player["score"] += 2
            coin_msg = "💰 撿到金幣 +2 分！"
        else:
            coin_msg = ""

        player["quiz"] = None
        player["last_quiz"] = None
        return (
            render_race(player["car_pos"]) +
            f"\n✅ 回答正確！{nitro_msg} {coin_msg}\n請輸入『前進』以獲得新題目！"
        )
    else:
        # 錯誤：扣燃料
        player["fuel"] -= 1
        if player["fuel"] <= 0:
            players.pop(user)
            return "🛑 油料耗盡，遊戲結束！輸入 '主選單' 重新開始"
        return (
            render_race(player["car_pos"], kana, choice_map) +
            "\n❌ 回答錯誤，燃料 -1！請再試一次！"
        )


# 🏎 賽車遊戲邏輯

def race_game(user):
    if user not in players:
        # 初始化
        coins = set(random.sample(range(1, track_length - 1), 3))  # 三顆金幣
        players[user] = {
            "car_pos": 0,
            "game": "race",
            "quiz": None,
            "fuel": 3,
            "score": 0,
            "coins": coins,
            "nitro": 0,
        }
    player = players[user]

    # 若先前已有題目
    if player.get("quiz"):
        kana, correct, choice_map = player["quiz"]
        player["last_quiz"] = (kana, correct, choice_map)
        global current_player
        current_player = player
        return render_race(player["car_pos"], kana, choice_map)

    # 產生新題目
    kana, correct = random.choice(list(kana_dict.items()))
    options = [correct]
    while len(options) < 3:
        distractor = random.choice(list(kana_dict.values()))
        if distractor not in options:
            options.append(distractor)
    random.shuffle(options)
    choice_map = {"A": options[0], "B": options[1], "C": options[2]}
    player["quiz"] = (kana, correct, choice_map)
    player["last_quiz"] = (kana, correct, choice_map)

    global current_player
    current_player = player
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
