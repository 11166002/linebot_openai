from flask import Flask, request, jsonify
import random
import time
import requests

app = Flask(__name__)

# ========== LINE Token ==========
CHANNEL_ACCESS_TOKEN = "你的 liqx01baPcbWbRF5if7oqBsZyf2+2L0eTOwvbIJ6f2Wec6is4sVd5onjl4fQAmc4n8EuqMfo7prlaG5la6kXb/y1gWOnk8ztwjjx2ZnukQbPJQeDwwcPEdFTOGOmQ1t88bQLvgQVczlzc/S9Q/6y5gdB04t89/1O/w1cDnyilFU="

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

kana_table_rows = [
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
]

# ========== 迷宮設定 ==========
maze = [
    ["⬛", "⬛", "⬛", "⬛", "⬛", "⬛", "⬛"],
    ["⬛", "⬜", "⬛", "⬛", "⬛", "⬛", "⬛"],
    ["⬛", "⬛", "⬜", "⬛", "⬛", "⬜", "⛩️"],
    ["⬛", "⬜", "⬜", "⬛", "⬛", "⬛", "⬛"],
    ["⬛", "⬛", "⬛", "⬛", "⬛", "⬛", "⬛"],
    ["⬛", "⬛", "⬛", "⬛", "⬛", "⬛", "⬛"]
]

movable = [(1,1), (1,2), (2,1), (2,2), (3,1), (4,1), (4,2), (5,1)]
goal = (2,6)
quiz_positions = [(2,3), (3,4)]
players = {}

# ========== 賽車遊戲設定 ==========
racers = {}

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
                flex_message = {
                    "type": "flex",
                    "altText": "請選擇功能",
                    "contents": {
                        "type": "bubble",
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "md",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "請選擇功能",
                                    "size": "lg",
                                    "weight": "bold"
                                },
                                {
                                    "type": "button",
                                    "style": "primary",
                                    "action": {
                                        "type": "message",
                                        "label": "🏎️ 賽車遊戲",
                                        "text": "我要玩賽車遊戲"
                                    }
                                },
                                {
                                    "type": "button",
                                    "style": "primary",
                                    "action": {
                                        "type": "message",
                                        "label": "📖 查看五十音",
                                        "text": "我要看五十音"
                                    }
                                },
                                {
                                    "type": "button",
                                    "style": "primary",
                                    "action": {
                                        "type": "message",
                                        "label": "🎮 開始迷宮遊戲",
                                        "text": "我要玩迷宮遊戲"
                                    }
                                }
                            ]
                        }
                    }
                }

                headers = {
                    "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
                    "Content-Type": "application/json"
                }
                body = {
                    "replyToken": reply_token,
                    "messages": [flex_message]
                }
                requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=body)

            elif text == "1" or text == "我要看五十音":
                reply_text(reply_token, get_kana_table())

            elif text == "2" or text == "我要玩迷宮遊戲":
                players[user_id] = {"pos": (1, 1), "quiz": None}
                reply_text(reply_token, render_map((1, 1)) + "\n\n遊戲開始！請輸入「上」「下」「左」「右」移動。")

            elif text == "3" or text == "我要玩賽車遊戲":
                racers[user_id] = {"pos": 0, "target": random.choice(list(kana_dict.items())), "start_time": time.time(), "lives": 3, "score": 0}
                kana, _ = racers[user_id]["target"]
                reply_text(reply_token, f"🏁 賽車遊戲開始！30 秒內完成 5 題並保住 3 條命。\n請輸入「{kana}」的羅馬拼音來推進賽車！")

            elif text in ["上", "下", "左", "右"]:
                result = maze_game(user_id, text)
                reply_text(reply_token, result["map"] + "\n\n" + result["message"])

            elif text in ["前進", "加速", "減速"]:
                result = racing_game(user_id, text)
                reply_text(reply_token, result["message"])

            else:
                reply_text(reply_token, "請輸入：\n「主選單」開啟選單\n「上/下/左/右」操作遊戲\n「前進/加速/減速」操作賽車遊戲")

    return "OK", 200

def get_kana_table():
    table = "\U0001F4D6 日語五十音對照表\n\n平假名\t片假名\t羅馬拼音\n" + ("-" * 28) + "\n"
    for h, k, r in kana_table_rows:
        table += f"{h}\t{k}\t{r}\n"
    return table

def maze_game(user, message):
    if user not in players:
        players[user] = {"pos": (1, 1), "quiz": None}

    player = players[user]

    if player["quiz"]:
        kana, answer = player["quiz"]
        if message.lower() == answer:
            player["quiz"] = None
            return {"map": render_map(player["pos"]), "message": "✅ 回答正確，繼續前進！"}
        else:
            return {"map": render_map(player["pos"]), "message": f"❌ 錯誤！再試一次：「{kana}」的羅馬拼音是？"}

    direction = {"上": (-1, 0), "下": (1, 0), "左": (0, -1), "右": (0, 1)}
    if message not in direction:
        return {"map": render_map(player["pos"]), "message": "請輸入方向：上、下、左、右"}

    dy, dx = direction[message]
    y, x = player["pos"]
    new_pos = (y + dy, x + dx)

    if new_pos not in movable:
        return {"map": render_map(player["pos"]), "message": "🚧 前方是牆，不能走喔！"}

    player["pos"] = new_pos

    if new_pos == goal:
        players.pop(user)
        return {"map": render_map(new_pos), "message": "🎉 恭喜你到達終點！遊戲完成！"}

    if new_pos in quiz_positions:
        kana, roma = random.choice(list(kana_dict.items()))
        player["quiz"] = (kana, roma)
        return {"map": render_map(new_pos), "message": f"❓ 挑戰：「{kana}」的羅馬拼音是？請輸入答案"}

    return {"map": render_map(new_pos), "message": "你移動了，可以繼續前進"}

def racing_game(user, message):
    if user not in racers:
        racers[user] = {"pos": 0, "target": random.choice(list(kana_dict.items())), "start_time": time.time(), "lives": 3, "score": 0}

    player = racers[user]
    race_status = player["race"]

    if message == "前進":
        player["race"] = "你在賽道上行駛中！"
        return {"message": "🏎️ 你已經前進！"}

    elif message == "加速":
        player["race"] = "你加速了！"
        return {"message": "⚡ 你加速了，速度更快！"}

    elif message == "減速":
        player["race"] = "你減速了！"
        return {"message": "⚠️ 你減速了，小心！"}

    return {"message": "請選擇行駛方向：「前進」、「加速」、「減速」"}

def render_map(player_pos):
    result = ""
    for y in range(6):
        for x in range(6):
            result += "🟩" if (y,x) == player_pos else maze[y][x]
        result += "\n"
    return result.strip()

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

if __name__ == "__main__":
    app.run(debug=True)
