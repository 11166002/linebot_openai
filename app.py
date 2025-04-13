from flask import Flask, request, jsonify
import random
import requests

app = Flask(__name__)

# ========== LINE Token ==========
CHANNEL_ACCESS_TOKEN = "你的 Channel Access Token"

# ========== 五十音資料 ==========
kana_dict = {
    "あ": "a", "い": "i", "う": "u", "え": "e", "お": "o",
    "か": "ka", "き": "ki", "く": "ku", "け": "ke", "こ": "ko",
    "さ": "sa", "し": "shi", "す": "su", "せ": "se", "そ": "so",
    "た": "ta", "ち": "chi", "つ": "tsu", "て": "te", "と": "to",
    "な": "na", "に": "ni", "ぬ": "nu", "ね": "ne", "の": "no",
    "は": "ha", "ひ": "hi", "ふ": "fu", "へ": "he", "ほ": "ho",
    "ま": "ma", "み": "mi", "む": "mu", "め": "me", "も": "mo",
    "や": "ya", "ゆ": "yu", "よ": "yo",
    "ら": "ra", "り": "ri", "る": "ru", "れ": "re", "ろ": "ro",
    "わ": "wa", "を": "wo", "ん": "n",
    "が": "ga", "ぎ": "gi", "ぐ": "gu", "げ": "ge", "ご": "go",
    "ざ": "za", "じ": "ji", "ず": "zu", "ぜ": "ze", "ぞ": "zo",
    "だ": "da", "ぢ": "ji", "づ": "zu", "で": "de", "ど": "do",
    "ば": "ba", "び": "bi", "ぶ": "bu", "べ": "be", "ぼ": "bo",
    "ぱ": "pa", "ぴ": "pi", "ぷ": "pu", "ぺ": "pe", "ぽ": "po",
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
}

# ========== 迷宮設定 ==========
maze_size = 7
maze = [["⬜" for _ in range(maze_size)] for _ in range(maze_size)]
for i in range(maze_size):
    maze[0][i] = maze[maze_size-1][i] = "⬛"
    maze[i][0] = maze[i][maze_size-1] = "⬛"

# 隨機牆壁
for _ in range(15):
    y, x = random.randint(1, maze_size-2), random.randint(1, maze_size-2)
    maze[y][x] = "⬛"

start = (1,1)
goal = (maze_size-2, maze_size-2)
maze[goal[0]][goal[1]] = "⛩️"
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

          
1️⃣ 我要看五十音
2️⃣ 我要玩迷宮遊戲
3️⃣ 我要玩賽車遊戲

【遊戲規則】
📘 看五十音：查看所有平假名、片假名與羅馬拼音對照。
🧩 迷宮遊戲：移動到終點途中會遇到假名選擇題，答對才能繼續。
🏎️ 賽車遊戲：每次輸入『前進』會推進一格，抵達終點即勝利！")

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
                reply_text(reply_token, "請輸入：\n「主選單」開啟選單\n「上/下/左/右」操作遊戲")

    return "OK", 200

def maze_game(user, message):
    if user not in players:
        players[user] = {"pos": start, "quiz": None, "game": "maze"}

    player = players[user]

    if player["quiz"]:
        kana, answer, choice_map = player["quiz"]
        if message.upper() in choice_map and choice_map[message.upper()] == answer:
            player["quiz"] = None
            return {"map": render_map(player["pos"]), "message": "✅ 回答正確，繼續前進！"}
        else:
            options_text = "\n".join([f"{key}. {val}" for key, val in choice_map.items()])
            return {"map": render_map(player["pos"]), "message": f"❌ 錯誤！再試一次：「{kana}」的羅馬拼音是？\n{options_text}"}

    direction = {"上": (-1, 0), "下": (1, 0), "左": (0, -1), "右": (0, 1)}
    if message not in direction:
        return {"map": render_map(player["pos"]), "message": "請輸入方向：上、下、左、右"}

    dy, dx = direction[message]
    y, x = player["pos"]
    new_pos = (y + dy, x + dx)

    if not (0 <= new_pos[0] < maze_size and 0 <= new_pos[1] < maze_size) or maze[new_pos[0]][new_pos[1]] == "⬛":
        return {"map": render_map(player["pos"]), "message": "🚧 前方是牆，不能走喔！"}

    player["pos"] = new_pos

    if new_pos == goal:
        players.pop(user)
        return {"map": render_map(new_pos), "message": "🎉 恭喜你到達終點！遊戲完成！\n輸入「主選單」重新開始"}

    if new_pos in quiz_positions:
        kana, correct = random.choice(list(kana_dict.items()))
        options = [correct]
        while len(options) < 3:
            distractor = random.choice(list(kana_dict.values()))
            if distractor not in options:
                options.append(distractor)
        random.shuffle(options)
        choice_map = {"A": options[0], "B": options[1], "C": options[2]}
        player["quiz"] = (kana, correct, choice_map)
        options_text = "\n".join([f"{key}. {val}" for key, val in choice_map.items()])
        return {"map": render_map(new_pos), "message": f"❓ 挑戰：「{kana}」的羅馬拼音是？請從下列選項選擇：\n{options_text}"}

    return {"map": render_map(new_pos), "message": "你移動了，可以繼續前進"}

def render_map(player_pos):
    result = ""
    for y in range(maze_size):
        for x in range(maze_size):
            if (y, x) == player_pos:
                result += "😊"
            elif (y, x) == goal:
                result += random.choice(["⛩️", "✨", "💫"])
            else:
                result += maze[y][x]
        result += "\n"
    return result.strip()

def render_race(pos):
    track = ["⬜" for _ in range(10)]
    if pos >= len(track):
        return "🏁 你贏了！賽車抵達終點！\n輸入「主選單」重新開始"
    track[pos] = "🏎️"
    return "🚗 賽車進度：\n" + ''.join(track)

def race_game(user):
    if user not in players:
        players[user] = {"car_pos": 0, "game": "race"}
    players[user]["car_pos"] += 1
    return render_race(players[user]["car_pos"])

def get_kana_table():
    # （保留原函數內容不變，省略重複顯示）
    return "(請將這裡補上你整理好的五十音對照表內容)"

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
