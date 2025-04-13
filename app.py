from flask import Flask, request, jsonify
import time
import random
import requests

app = Flask(__name__)

# ========== LINE Token ==========
CHANNEL_ACCESS_TOKEN = "你的 Channel Access Token"

# ========== 五十音資料 ==========
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
    ["⬜"  // 替換黑方塊為白底灰框方塊表示牆壁
    }
  ]
}", "⬛", "⬛", "⬛", "⬛", "⬛", "⬛"],
    ["⬛", "⬜", "⬜", "⬛", "⬜", "⬜", "⬛"],
    ["⬛", "⬛", "⬜", "⬛", "⬛", "⬜", "⛩️"],
    ["⬛", "⬜", "⬜", "⬜", "⬛", "⬛", "⬛"],
    ["⬛", "⬜", "⬛", "⬜", "⬜", "⬜", "⬛"],
    ["⬛", "⬜", "⬛", "⬛", "⬛", "⬜", "⬛"],
    ["⬛", "⬛", "⬛", "⬛", "⬛", "⬛", "⬛"]
],
    ["⬛", "⬜", "⬜", "⬛", "⬛"],
    ["⬛", "⬜", "⬜", "⬛", "⛩️"],
    ["⬛", "⬜", "⬛", "⬛", "⬛"],
    ["⬛", "⬛", "⬛", "⬛", "⬛"]
]

movable = [
    (1,1), (1,2), (1,4), (1,5),
    (2,2), (2,5), (2,6),
    (3,1), (3,2), (3,3),
    (4,1), (4,3), (4,4), (4,5),
    (5,1), (5,5)
]
goal = (2,6)
quiz_positions = [(2,2), (3,1), (4,3), (4,5)]
players = {}
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
                                    "type": "image",
                                    "url": "https://i.imgur.com/VFegO6L.png",
                                    "size": "full",
                                    "aspectMode": "cover",
                                    "aspectRatio": "20:13"
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
                                },
                                {
                                    "type": "button",
                                    "style": "secondary",
                                    "action": {
                                        "type": "message",
                                        "label": "ℹ️ 遊戲說明",
                                        "text": "遊戲說明"
                                    }
                                },
                                {
                                    "type": "button",
                                    "style": "secondary",
                                    "action": {
                                        "type": "message",
                                        "label": "❌ 離開遊戲",
                                        "text": "退出遊戲"
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
                reply_text(reply_token, "🏯 歡迎進入迷宮遊戲！

你將透過輸入「上」「下」「左」「右」來控制角色移動，在迷宮中前進，答對五十音題目，成功抵達⛩️終點！

📌 每走幾步會有題目，請輸入正確的羅馬拼音答題。
📌 接近終點會有鼓勵提示，加油！

⬜ 牆壁
🚪 你的位置
⛩️ 終點

👉 準備好了嗎？請輸入：「我迫不及待要玩啦」開始遊戲！")
                players[user_id] = {"pos": (1,1), "quiz": None}
                reply_text(reply_token, render_map((1,1)) + "\n\n遊戲開始！請輸入「上」「下」「左」「右」移動。")

            elif text == "我迫不及待要玩啦":
                players[user_id] = {"pos": (1,1), "quiz": None}
                reply_text(reply_token, render_map((1,1)) + "

遊戲開始！請輸入「上」「下」「左」「右」移動。")

            elif text in ["上", "下", "左", "右"]:
                result = maze_game(user_id, text)
                reply_text(reply_token, result["map"] + "\n\n" + result["message"])

            elif text == "我要玩賽車遊戲":
                reply_token_headers = {
                    "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
                    "Content-Type": "application/json"
                }
                guide_with_image = {
                    "replyToken": reply_token,
                    "messages": [
                        {
                            "type": "image",
                            "originalContentUrl": "https://files.chatbox.com/cdn/file_00000000919462309efeeaa53b057f54.png",
                            "previewImageUrl": "https://files.chatbox.com/cdn/file_00000000919462309efeeaa53b057f54.png"
                        },
                        {
                            "type": "text",
                            "text": "🏎️ 賽車遊戲說明：\n你將在 30 秒內答對五十音拼音，推進賽車，每題加 10 分，答錯扣 1 條命（共三條）。完成 5 題即衝線獲勝！\n\n👉 輸入：「我準備好要開車啦」開始遊戲！"
                        }
                    ]
                }
                requests.post("https://api.line.me/v2/bot/message/reply", headers=reply_token_headers, json=guide_with_image)
                racers[user_id] = {"pos": 0, "target": random.choice(list(kana_dict.items())), "start_time": time.time(), "lives": 3, "score": 0}
                kana, _ = racers[user_id]["target"]
                reply_text(reply_token, f"🏁 賽車遊戲開始！30 秒內完成 5 題並保住 3 條命。
請輸入「{kana}」的羅馬拼音來推進賽車！")

            elif text == "我準備好要開車啦":
                racers[user_id] = {"pos": 0, "target": random.choice(list(kana_dict.items())), "start_time": time.time(), "lives": 3, "score": 0}
                kana, _ = racers[user_id]["target"]
                reply_text(reply_token, f"🏁 賽車遊戲開始！\n請輸入「{kana}」的羅馬拼音來推進賽車！")

            elif user_id in racers:
                elapsed = time.time() - racers[user_id].get("start_time", 0)
                if elapsed > 30:
                    del racers[user_id]
                    reply_text(reply_token, "⏰ 時間到！你沒在 30 秒內完成賽車遊戲。")
                    return

                kana, correct = racers[user_id]["target"]
                if text.lower() == correct:
                    racers[user_id]["pos"] += 1
                    racers[user_id]["score"] += 10
                    if racers[user_id]["pos"] >= 5:
                        score = racers[user_id]["score"]
                        del racers[user_id]
                        reply_text(reply_token, f"🎉 衝線成功！你完成了賽車挑戰！
最終得分：{score} 分")
                    else:
                        racers[user_id]["target"] = random.choice(list(kana_dict.items()))
                        next_kana, _ = racers[user_id]["target"]
                        track = "🚗" + "━" * racers[user_id]["pos"] + "🏁"
                        reply_text(reply_token, f"✅ 正確！你已推進 {racers[user_id]['pos']} 格
{track}
💯 分數：{racers[user_id]['score']}
❤️ 剩餘命數：{racers[user_id]['lives']}
下一題：「{next_kana}」 的羅馬拼音是？")
                else:
                    racers[user_id]["lives"] -= 1
                    if racers[user_id]["lives"] <= 0:
                        del racers[user_id]
                        reply_text(reply_token, "💥 你失去所有命，遊戲結束！")
                    else:
                        reply_text(reply_token, f"❌ 錯誤！再試一次：「{kana}」的羅馬拼音是？
❤️ 剩餘命數：{racers[user_id]['lives']}")
                        racers[user_id]["target"] = random.choice(list(kana_dict.items()))
                        next_kana, _ = racers[user_id]["target"]
                        track = "🚗" + "━" * racers[user_id]["pos"] + "🏁"
                        reply_text(reply_token, f"正確！你已推進：{racers[user_id]['pos']} 格
{track}
下一題：「{next_kana}」 的羅馬拼音是？")
                else:
                    reply_text(reply_token, f"❌ 錯誤，再試一次：「{kana}」的羅馬拼音是？")

            elif user_id in players and players[user_id]["quiz"]:
                result = maze_game(user_id, text)
                reply_text(reply_token, result["map"] + "\n\n" + result["message"])

            else:
                reply_text(reply_token, "請輸入：\n「主選單」開啟選單\n「上/下/左/右」操作遊戲")

    return "OK", 200

def get_kana_table():
    table = "\U0001F4D6 日語五十音對照表\n\n平假名\t片假名\t羅馬拼音\n" + ("-" * 28) + "\n"
    for h, k, r in kana_table_rows:
        table += f"{h}\t{k}\t{r}\n"
    return table

def maze_game(user, message):
    if user not in players:
        players[user] = {"pos": (1,1), "quiz": None}

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
        # 如果玩家靠近終點前一格，打開周圍牆壁作為動態機關
        if abs(new_pos[0] - goal[0]) + abs(new_pos[1] - goal[1]) == 1:
            movable.append(goal)
            return {"map": render_map(player["pos"]), "message": "🌀 終點前的門打開了！快往⛩️前進！"}

        return {"map": render_map(player["pos"]), "message": "🚧 前方是牆，不能走喔！"}

    player["pos"] = new_pos

    if abs(new_pos[0] - goal[0]) + abs(new_pos[1] - goal[1]) == 1:
        return {"map": render_map(new_pos), "message": "💯 加油加油！剩一步囉！快到終點！
🎉🎉🎉"}

    if new_pos == goal:
        players.pop(user)
        return {"map": render_map(new_pos), "message": "🎉 恭喜你到達終點！遊戲完成！"}

    if new_pos in quiz_positions:
        kana, roma = random.choice(list(kana_dict.items()))
        player["quiz"] = (kana, roma)
        return {"map": render_map(new_pos), "message": f"❓ 挑戰：「{kana}」的羅馬拼音是？請輸入答案"}

    return {"map": render_map(new_pos), "message": "你移動了，可以繼續前進"}

def render_map(player_pos):
    result = ""
    for y in range(5):
        for x in range(5):
            if (y,x) == player_pos:
            result += "🚪"  # 玩家入口圖示  # 😊 玩家位置
            elif (y,x) == goal:
                result += random.choice(["⛩️", "✨", "💫"])  # 閃爍終點效果
            else:
                result += maze[y][x]
        result += "
"
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
