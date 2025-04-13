# --- 完整修正後的 LINE Bot 遊戲程式碼 v1.0 ---
# 說明：本程式整合 LINE Flex Menu、日語五十音查詢、迷宮遊戲、賽車遊戲

from flask import Flask, request, jsonify
import random
import time
import requests

app = Flask(__name__)

# LINE Token 設定
CHANNEL_ACCESS_TOKEN = "liqx01baPcbWbRF5if7oqBsZyf2+2L0eTOwvbIJ6f2Wec6is4sVd5onjl4fQAmc4n8EuqMfo7prlaG5la6kXb/y1gWOnk8ztwjjx2ZnukQbPJQeDwwcPEdFTOGOmQ1t88bQLvgQVczlzc/S9Q/6y5gdB04t89/1O/w1cDnyilFU="

# 玩家狀態
players = {}
racers = {}

# 五十音對照表（節錄清音）
kana_dict = {
    # 清音
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
    # 濁音
    "が": "ga", "ぎ": "gi", "ぐ": "gu", "げ": "ge", "ご": "go",
    "ざ": "za", "じ": "ji", "ず": "zu", "ぜ": "ze", "ぞ": "zo",
    "だ": "da", "ぢ": "ji", "づ": "zu", "で": "de", "ど": "do",
    "ば": "ba", "び": "bi", "ぶ": "bu", "べ": "be", "ぼ": "bo",
    # 半濁音
    "ぱ": "pa", "ぴ": "pi", "ぷ": "pu", "ぺ": "pe", "ぽ": "po",
    # 拗音
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

# 五十音查表資料
kana_table_rows = [
    ("あ", "ア", "a"), ("い", "イ", "i"), ("う", "ウ", "u"), ("え", "エ", "e"), ("お", "オ", "o"),
    ("か", "カ", "ka"), ("き", "キ", "ki"), ("く", "ク", "ku"), ("け", "ケ", "ke"), ("こ", "コ", "ko"),
    ("さ", "サ", "sa"), ("し", "シ", "shi"), ("す", "ス", "su"), ("せ", "セ", "se"), ("そ", "ソ", "so")
]

# 地圖設定
maze = [
    ["⬛", "⬛", "⬛", "⬛", "⬛", "⬛", "⬛"],
    ["⬛", "⬜", "⬛", "⬜", "⬜", "⬛", "⬛"],
    ["⬛", "⬜", "⬛", "⬛", "⬜", "⬜", "⛩️"],
    ["⬛", "⬜", "⬜", "⬜", "⬛", "⬛", "⬛"],
    ["⬛", "⬛", "⬛", "⬛", "⬛", "⬛", "⬛"]
]
]
movable = [(1,1), (1,3), (1,4), (2,1), (2,4), (2,5), (2,6), (3,1), (3,2), (3,3)]
quiz_positions = [(2,1), (3,2), (1,4)]
goal = (2,4)

@app.route("/callback", methods=["POST"])
def callback():
    body = request.get_json()
    events = body.get("events", [])

    for event in events:
        if event["type"] == "message":
            user_id = event["source"]["userId"]
            reply_token = event["replyToken"]
            text = event["message"]["text"].strip()

            if text == "我要看五十音":
                reply_text(reply_token, get_kana_table())

            elif text == "我要玩迷宮遊戲":
                reply_text(reply_token, "🌀【迷宮遊戲說明】
你將控制主角在迷宮中前進，通過日語五十音挑戰才能到達終點！
⬜ 可走的路｜⬛ 牆壁｜⛩️ 終點
請使用『上／下／左／右』來移動角色，部分格子會隨機出題！
⚠️ 本關迷宮較複雜，請小心探索！")
                
                players[user_id] = {"pos": (1,1), "quiz": None}
                reply_text(reply_token, render_map((1,1)) + "

🎮 遊戲開始！請輸入 上 / 下 / 左 / 右")
                players[user_id] = {"pos": (1,1), "quiz": None}
                reply_text(reply_token, render_map((1,1)) + "\n\n遊戲開始！請輸入 上 / 下 / 左 / 右")

            elif text in ["上", "下", "左", "右"]:
                if user_id in players:
                    result = maze_game(user_id, text)
                    reply_text(reply_token, result["map"] + "\n\n" + result["message"])

            elif text == "我要玩賽車遊戲":
                reply_text(reply_token, "🏎️【賽車遊戲說明】
你需要在 30 秒內正確答出 8 題五十音羅馬拼音，每答對一題，賽車將向終點推進一格！
💥 答錯會扣命，最多 3 次機會，來挑戰你的反應與記憶吧！")
                racers[user_id] = {"pos": 0, "target": random.choice(list(kana_dict.items())), "start_time": time.time(), "lives": 3, "score": 0}
                kana, _ = racers[user_id]["target"]
                reply_text(reply_token, f"🏁 賽車遊戲開始！請輸入「{kana}」的羅馬拼音來推進！")
                racers[user_id] = {"pos": 0, "target": random.choice(list(kana_dict.items())), "start_time": time.time(), "lives": 3, "score": 0}
                kana, _ = racers[user_id]["target"]
                reply_text(reply_token, f"🏁 賽車遊戲開始！請輸入「{kana}」的羅馬拼音來推進！")

            elif text.lower() in kana_dict.values() and user_id in racers:
                racer = racers[user_id]
                elapsed = time.time() - racer["start_time"]
                if elapsed > 30:
                    del racers[user_id]
                    reply_text(reply_token, "⏰ 時間到！賽車遊戲結束！")
                    return
                correct = racer["target"][1]
                if text.lower() == correct:
                    racer["pos"] += 1
                    racer["score"] += 10
                    if racer["pos"] >= 8:
                        score = racer["score"]
                        del racers[user_id]
                        reply_text(reply_token, f"🎉 衝線成功！得分：{score}")
                    else:
                        racer["target"] = random.choice(list(kana_dict.items()))
                        next_kana = racer["target"][0]
                        track = "🚗" + "━" * racer["pos"] + "🏁"
                        reply_text(reply_token, f"✅ 正確！\n{track}\n下一題：「{next_kana}」的羅馬拼音是？")
                else:
                    racer["lives"] -= 1
                    if racer["lives"] <= 0:
                        del racers[user_id]
                        reply_text(reply_token, "💥 你失去所有命，遊戲結束！")
                    else:
                        reply_text(reply_token, f"❌ 錯誤！剩餘命數：{racer['lives']}")

    return "OK", 200

def get_kana_table():
    table = "📖 日語五十音對照表\n\n平假名\t片假名\t羅馬拼音\n" + "-" * 30 + "\n"
    for h, k, r in kana_table_rows:
        table += f"{h}\t{k}\t{r}\n"
    return table

def maze_game(user, direction):
    dirs = {"上": (-1,0), "下": (1,0), "左": (0,-1), "右": (0,1)}
    dy, dx = dirs[direction]
    y, x = players[user]["pos"]
    new_pos = (y+dy, x+dx)

    if new_pos not in movable:
        return {"map": render_map(players[user]["pos"]), "message": "🚧 前方是牆！"}

    players[user]["pos"] = new_pos

    if new_pos == goal:
        del players[user]
        return {"map": render_map(new_pos), "message": "🎉 恭喜你到達終點！"}

    if new_pos in quiz_positions:
        kana, roma = random.choice(list(kana_dict.items()))
        players[user]["quiz"] = (kana, roma)
        return {"map": render_map(new_pos), "message": f"❓ 請輸入「{kana}」的羅馬拼音："}

    if players[user].get("quiz"):
        kana, answer = players[user]["quiz"]
        if direction.lower() == answer:
            players[user]["quiz"] = None
            return {"map": render_map(new_pos), "message": "✅ 答對了！繼續前進！"}
        else:
            return {"map": render_map(new_pos), "message": f"❌ 錯誤！請再輸入「{kana}」的拼音。"}

    return {"map": render_map(new_pos), "message": "繼續前進中..."}

def render_map(player_pos):
    result = ""
    for y in range(len(maze)):
        for x in range(len(maze[0])):
            if (y,x) == player_pos:
                result += "🚪"
            elif (y,x) == goal:
                result += random.choice(["⛩️", "✨"])
            else:
                result += maze[y][x]
        result += "\n"
    return result

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
