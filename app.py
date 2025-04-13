from flask import Flask, request, jsonify
import random
import requests

app = Flask(__name__)

# ========== LINE Token ==========
CHANNEL_ACCESS_TOKEN = "liqx01baPcbWbRF5if7oqBsZyf2+2L0eTOwvbIJ6f2Wec6is4sVd5onjl4fQAmc4n8EuqMfo7prlaG5la6kXb/y1gWOnk8ztwjjx2ZnukQbPJQeDwwcPEdFTOGOmQ1t88bQLvgQVczlzc/S9Q/6y5gdB04t89/1O/w1cDnyilFU="

# ========== 五十音資料 ==========
kana_dict = {}

# 清音
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

# 濁音
kana_dict.update({
    "が": "ga", "ぎ": "gi", "ぐ": "gu", "げ": "ge", "ご": "go",
    "ざ": "za", "じ": "ji", "ず": "zu", "ぜ": "ze", "ぞ": "zo",
    "だ": "da", "ぢ": "ji", "づ": "zu", "で": "de", "ど": "do",
    "ば": "ba", "び": "bi", "ぶ": "bu", "べ": "be", "ぼ": "bo"
})

# 半濁音
kana_dict.update({
    "ぱ": "pa", "ぴ": "pi", "ぷ": "pu", "ぺ": "pe", "ぽ": "po"
})

# 拗音
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

# ========== 迷宮設定 ==========
maze_size = 7
maze = [["⬜" for _ in range(maze_size)] for _ in range(maze_size)]
for i in range(maze_size):
    maze[0][i] = maze[maze_size-1][i] = "⬛"
    maze[i][0] = maze[i][maze_size-1] = "⬛"

# 隨機牆壁（避免蓋到起點與終點）
for _ in range(8):
    while True:
        y, x = random.randint(1, maze_size - 2), random.randint(1, maze_size - 2)
        if (y, x) != start and (y, x) != goal and maze[y][x] != "⬛":
            maze[y][x] = "⬛"
            break

start = (1,1)
goal = (maze_size-2, maze_size-2)
maze[goal[0]][goal[1]] = "⛩"
players = {}
quiz_positions = [(random.randint(1, maze_size-2), random.randint(1, maze_size-2)) for _ in range(5)]

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
    "2. 我要玩迷宮遊戲\n"
    "3. 我要玩賽車遊戲\n\n"
    "【遊戲規則】\n"
    "📘 看五十音：查看所有平假名、片假名與羅馬拼音對照。\n"
    "🧩 迷宮遊戲：使用『上/下/左/右』移動角色，遇到假名選擇題時答對才能繼續。\n"
    "🏎 賽車遊戲：每次輸入『前進』會推進一格，抵達終點即勝利！"
)

                reply_text(reply_token, menu)
          


            elif text == "1" or text == "我要看五十音":
                reply_text(reply_token, get_kana_table())

            elif text == "2" or text == "我要玩迷宮遊戲":
                players[user_id] = {"pos": start, "quiz": None, "game": "maze"}
                reply_text(reply_token, render_map(start) + "\n\n迷宮遊戲開始！請輸入「上」「下」「左」「右」移動。")

            elif text == "3" or text == "我要玩賽車遊戲":
                players[user_id] = {"car_pos": 0, "game": "race"}
                reply_text(reply_token, render_race(0) + "\n\n賽車遊戲開始！請輸入「前進」移動你的車。")

            elif user_id in players and players[user_id].get("game") == "maze" and text in ["上", "下", "左", "右"]:
                result = maze_game(user_id, text)
                reply_text(reply_token, result["map"] + "\n\n" + result["message"])

            elif user_id in players and players[user_id].get("game") == "maze" and players[user_id]["quiz"]:
                result = maze_game(user_id, text)
                reply_text(reply_token, result["map"] + "\n\n" + result["message"])

            elif user_id in players and players[user_id].get("game") == "race" and text == "前進":
                result = race_game(user_id)
                reply_text(reply_token, result)

            else:
                reply_text(reply_token, "訊息內容")

    return "OK", 200

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

def maze_game(user, message):
    player = players.setdefault(user, {"pos": start, "quiz": None, "game": "maze", "score": 0})

    # 題目處理
    if player.get("quiz"):
        kana, answer, choice_map = player["quiz"]
        if message in choice_map and choice_map[message] == answer:
            player["quiz"] = None
            return {"map": render_map(player["pos"]), "message": "✅ 回答正確，繼續前進！"}
        else:
            options_text = "
".join([f"{key}. {val}" for key, val in choice_map.items()]))
            return {"map": render_map(player["pos"]), "message": f"❌ 錯誤！再試一次：「{kana}」的羅馬拼音是？\n{options_text}"}

    # 移動處理
    direction = {"上": (-1, 0), "下": (1, 0), "左": (0, -1), "右": (0, 1)}
    if message not in direction:
        return {"map": render_map(player["pos"]), "message": "請輸入方向：上、下、左、右"}

    dy, dx = direction[message]
    y, x = player["pos"]
    new_pos = (y + dy, x + dx)

    if not (0 <= new_pos[0] < maze_size and 0 <= new_pos[1] < maze_size) or maze[new_pos[0]][new_pos[1]] == "⬛":
        return {"map": render_map(player["pos"]), "message": "🚧 前方是牆，不能走喔！"}

    player["pos"] = new_pos

    # 陷阱格（倒退一步）
    if new_pos in [(2, 2), (3, 3)]:
        player["pos"] = (max(1, new_pos[0] - 1), new_pos[1])
        return {"map": render_map(player["pos"]), "message": "💥 你踩到陷阱，退回一步！"}

    # 獎勵格（直接到終點）
    if new_pos == (2, 5):
        player["pos"] = goal
        return {"map": render_map(goal), "message": "🎁 幸運！你搭上瞬移傳送門，直達終點！"}

    if new_pos == goal:
        players.pop(user)
        return {"map": render_map(new_pos), "message": "🎉 恭喜你到達終點！遊戲完成！\n輸入 '主選單' 重新開始"}
    # 題目出題
    if new_pos in quiz_positions:
        kana, correct = random.choice(list(kana_dict.items()))
        options = [correct]
        while len(options) < 3:
            distractor = random.choice(list(kana_dict.values()))
            if distractor not in options:
                options.append(distractor)
        random.shuffle(options)
        choice_map = {"1": options[0], "2": options[1], "3": options[2]}
        player["quiz"] = (kana, correct, choice_map)
        player["score"] = player.get("score", 0) + 1
        options_text = "\n".join([f"{key}. {val}" for key, val in choice_map.items()])
        return {"map": render_map(new_pos), "message": f"❓ 挑戰：「{kana}」的羅馬拼音是？請從下列選項選擇：\n{options_text}"}
        return {"map": render_map(new_pos), "message": f"你移動了，可以繼續前進（得分 {player.get('score', 0)} 分）"}

    if new_pos in quiz_positions:
        kana, correct = random.choice(list(kana_dict.items()))
        options = [correct]
        while len(options) < 3:
            distractor = random.choice(list(kana_dict.values()))
            if distractor not in options:
                options.append(distractor)
        random.shuffle(options)
        choice_map = {"1": options[0], "2": options[1], "3": options[2]}
        player["quiz"] = (kana, correct, choice_map)
        player["score"] = player.get("score", 0) + 1  # 答對加分
        options_text = "\n".join([f"{key}. {val}" for key, val in choice_map.items()])
        return {"map": render_map(new_pos), "message": f"❓ 挑戰：「{kana}」的羅馬拼音是？請從下列選項選擇：\n{options_text}"}
        return {"map": render_map(new_pos), "message": f"你移動了，可以繼續前進（得分 {player.get('score', 0)} 分）"}

def render_map(player_pos):
    result = ""
    for y in range(maze_size):
        for x in range(maze_size):
            if (y, x) == player_pos:
                result += "😊"
            elif (y, x) == goal:
                result += "⛩"
            else:
                result += maze[y][x]
        result += "\n"
    return result.strip()

def render_race(pos, kana=None, options=None):
    track = ["⬜" for _ in range(10)]
    if pos >= len(track):
        return "🏁 你贏了！賽車抵達終點！\n輸入 '主選單' 重新開始"
    track[pos] = "🏎"
    race_line = "🚗 賽車進度：\n" + ''.join(track)
    if kana and options:
        options_text = "\n".join([f"{key}. {val}" for key, val in options.items()])
        return f"{race_line}\n\n❓ 請問「{kana}」的羅馬拼音是？\n{options_text}\n請輸入 1/2/3 作答。"
    return race_line

def race_game(user):
    if user not in players:
        players[user] = {"car_pos": 0, "game": "race", "quiz": None}

    player = players[user]

    # 若仍有題目等待作答
    if player.get("quiz"):
        kana, correct, choice_map = player["quiz"]
        player["quiz"] = None  # 清除後立即驗證輸入
        return render_race(player["car_pos"], kana, choice_map)

    # 題目正確後才推進
    last_msg = player.get("last_msg")
    if last_msg in ["A", "B", "C"]:
        kana, correct, choice_map = player["last_quiz"]
        if choice_map.get(last_msg) == correct:
            player["car_pos"] += 1
            player["last_msg"] = None
            player["last_quiz"] = None
        else:
            return render_race(player["car_pos"], kana, choice_map) + "\n❌ 錯誤，請再試一次！"


    # 新題目
    kana, correct = random.choice(list(kana_dict.items()))
    options = [correct]
    while len(options) < 3:
        distractor = random.choice(list(kana_dict.values()))
        if distractor not in options:
            options.append(distractor)
    random.shuffle(options)
    choice_map = {"1": options[0], "2": options[1], "3": options[2]}
    players[user]["quiz"] = (kana, correct, choice_map)
    players[user]["last_quiz"] = (kana, correct, choice_map)
    return render_race(player["car_pos"], kana, choice_map)

def get_kana_table():
    table = "【日語五十音對照表】
"

    groups = [
        ("清音", [
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
        ("濁音", [
            ("が", "ga"), ("ぎ", "gi"), ("ぐ", "gu"), ("げ", "ge"), ("ご", "go"),
            ("ざ", "za"), ("じ", "ji"), ("ず", "zu"), ("ぜ", "ze"), ("ぞ", "zo"),
            ("だ", "da"), ("ぢ", "ji"), ("づ", "zu"), ("で", "de"), ("ど", "do"),
            ("ば", "ba"), ("び", "bi"), ("ぶ", "bu"), ("べ", "be"), ("ぼ", "bo")
        ]),
        ("半濁音", [
            ("ぱ", "pa"), ("ぴ", "pi"), ("ぷ", "pu"), ("ぺ", "pe"), ("ぽ", "po")
        ]),
        ("拗音", [
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
        table += f"

【{title}】
"
    for i in range(0, len(kana_group), 5):
        row = kana_group[i:i+5]
        line = "  ".join([f"{kana} → {roma}" for kana, roma in row])
        table += line + "
"

    return table.strip()
