from flask import Flask, request, jsonify
import random
import requests

app = Flask(__name__)

# ========== LINE Token ==========
CHANNEL_ACCESS_TOKEN = "liqx01baPcbWbRF5if7oqBsZyf2+2L0eTOwvbIJ6f2Wec6is4sVd5onjl4fQAmc4n8EuqMfo7prlaG5la6kXb/y1gWOnk8ztwjjx2ZnukQbPJQeDwwcPEdFTOGOmQ1t88bQLvgQVczlzc/S9Q/6y5gdB04t89/1O/w1cDnyilFU="

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
    "わ": "wa", "を": "wo", "ん": "n"
}

kana_table_rows = [(h, k, kana_dict[h]) for h, k in zip(
    list("あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん"),
    list("アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン")
)]

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

            if text == "主選單":
                reply_text(reply_token, "請選擇：
1️⃣ 我要看五十音
2️⃣ 我要玩迷宮遊戲
3️⃣ 我要玩賽車遊戲")
                reply_text(reply_token, "請選擇：\n1️⃣ 我要看五十音\n2️⃣ 我要玩迷宮遊戲")

            elif text == "1" or text == "我要看五十音":
                reply_text(reply_token, get_kana_table())

            elif text == "2" or text == "我要玩迷宮遊戲":
                players[user_id] = {"pos": start, "quiz": None, "game": "maze"}
                reply_text(reply_token, render_map(start) + "

迷宮遊戲開始！請輸入「上」「下」「左」「右」移動。")

            elif text == "3" or text == "我要玩賽車遊戲":
                players[user_id] = {"car_pos": 0, "game": "race"}
                reply_text(reply_token, render_race(0) + "

賽車遊戲開始！請輸入「前進」移動你的車。")
                players[user_id] = {"pos": start, "quiz": None}
                reply_text(reply_token, render_map(start) + "\n\n遊戲開始！請輸入「上」「下」「左」「右」移動。")

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

def get_kana_table():
    sections = {
        "清音": [
            ("あ", "ア", "a"), ("い", "イ", "i"), ("う", "ウ", "u"), ("え", "エ", "e"), ("お", "オ", "o"),
            ("か", "カ", "ka"), ("き", "キ", "ki"), ("く", "ク", "ku"), ("け", "ケ", "ke"), ("こ", "コ", "ko"),
            ("さ", "サ", "sa"), ("し", "シ", "shi"), ("す", "ス", "su"), ("せ", "セ", "se"), ("そ", "ソ", "so"),
            ("た", "タ", "ta"), ("ち", "チ", "chi"), ("つ", "ツ", "tsu"), ("て", "テ", "te"), ("と", "ト", "to"),
            ("な", "ナ", "na"), ("に", "ニ", "ni"), ("ぬ", "ヌ", "nu"), ("ね", "ネ", "ne"), ("の", "ノ", "no"),
            ("は", "ハ", "ha"), ("ひ", "ヒ", "hi"), ("ふ", "フ", "fu"), ("へ", "ヘ", "he"), ("ほ", "ホ", "ho"),
            ("ま", "マ", "ma"), ("み", "ミ", "mi"), ("む", "ム", "mu"), ("め", "メ", "me"), ("も", "モ", "mo"),
            ("や", "ヤ", "ya"), ("ゆ", "ユ", "yu"), ("よ", "ヨ", "yo"),
            ("ら", "ラ", "ra"), ("り", "リ", "ri"), ("る", "ル", "ru"), ("れ", "レ", "re"), ("ろ", "ロ", "ro"),
            ("わ", "ワ", "wa"), ("を", "ヲ", "wo"), ("ん", "ン", "n")
        ],
        "濁音": [
            ("が", "ガ", "ga"), ("ぎ", "ギ", "gi"), ("ぐ", "グ", "gu"), ("げ", "ゲ", "ge"), ("ご", "ゴ", "go"),
            ("ざ", "ザ", "za"), ("じ", "ジ", "ji"), ("ず", "ズ", "zu"), ("ぜ", "ゼ", "ze"), ("ぞ", "ゾ", "zo"),
            ("だ", "ダ", "da"), ("ぢ", "ヂ", "ji"), ("づ", "ヅ", "zu"), ("で", "デ", "de"), ("ど", "ド", "do")
        ],
        "半濁音": [
            ("ば", "バ", "ba"), ("び", "ビ", "bi"), ("ぶ", "ブ", "bu"), ("べ", "ベ", "be"), ("ぼ", "ボ", "bo"),
            ("ぱ", "パ", "pa"), ("ぴ", "ピ", "pi"), ("ぷ", "プ", "pu"), ("ぺ", "ペ", "pe"), ("ぽ", "ポ", "po")
        ],
        "拗音": [
            ("きゃ", "キャ", "kya"), ("きゅ", "キュ", "kyu"), ("きょ", "キョ", "kyo"),
            ("しゃ", "シャ", "sha"), ("しゅ", "シュ", "shu"), ("しょ", "ショ", "sho"),
            ("ちゃ", "チャ", "cha"), ("ちゅ", "チュ", "chu"), ("ちょ", "チョ", "cho"),
            ("にゃ", "ニャ", "nya"), ("にゅ", "ニュ", "nyu"), ("にょ", "ニョ", "nyo"),
            ("ひゃ", "ヒャ", "hya"), ("ひゅ", "ヒュ", "hyu"), ("ひょ", "ヒョ", "hyo"),
            ("みゃ", "ミャ", "mya"), ("みゅ", "ミュ", "myu"), ("みょ", "ミョ", "myo"),
            ("りゃ", "リャ", "rya"), ("りゅ", "リュ", "ryu"), ("りょ", "リョ", "ryo"),
            ("ぎゃ", "ギャ", "gya"), ("ぎゅ", "ギュ", "gyu"), ("ぎょ", "ギョ", "gyo"),
            ("じゃ", "ジャ", "ja"), ("じゅ", "ジュ", "ju"), ("じょ", "ジョ", "jo"),
            ("びゃ", "ビャ", "bya"), ("びゅ", "ビュ", "byu"), ("びょ", "ビョ", "byo"),
            ("ぴゃ", "ピャ", "pya"), ("ぴゅ", "ピュ", "pyu"), ("ぴょ", "ピョ", "pyo")
        ]
    }

    table = "📖 日語五十音對照表
"
    for title, rows in sections.items():
        table += f"
【{title}】
平假名	片假名	羅馬拼音
" + ("-" * 28) + "
"
        for h, k, r in rows:
            table += f"{h}	{k}	{r}
"
    return table

def maze_game(user, message):
    if user not in players:
        players[user] = {"pos": start, "quiz": None}

    player = players[user]

    if player["quiz"]:
        kana, answer, choice_map = player["quiz"]
        if message.upper() in choice_map and choice_map[message.upper()] == answer:
            player["quiz"] = None
            return {"map": render_map(player["pos"]), "message": "✅ 回答正確，繼續前進！"}
        else:
            options_text = "
".join([f"{key}. {val}" for key, val in choice_map.items()])
            return {"map": render_map(player["pos"]), "message": f"❌ 錯誤！再試一次：「{kana}」的羅馬拼音是？
{options_text}"}

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
        options_text = "
".join([f"{key}. {val}" for key, val in choice_map.items()])
        return {"map": render_map(new_pos), "message": f"❓ 挑戰：「{kana}」的羅馬拼音是？請從下列選項選擇：
{options_text}"}
        player["quiz"] = (kana, roma)
        return {"map": render_map(new_pos), "message": f"❓ 挑戰：「{kana}」的羅馬拼音是？請輸入答案"}

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
        return "🏁 你贏了！賽車抵達終點！
輸入「主選單」重新開始"
    track[pos] = "🏎️"
    return "🚗 賽車進度：
" + ''.join(track)

def race_game(user):
    if user not in players:
        players[user] = {"car_pos": 0, "game": "race"}
    players[user]["car_pos"] += 1
    return render_race(players[user]["car_pos"])


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
