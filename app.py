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
# 🗂️ Google Drive 上每個假名對應的 wav 檔案 ID
drive_id_map = {
    "あ": "1qi4Wzop1HRLWE8FjnjlmhWrdqGYf0TK-",
    "い": "1eX0J_ldzEauj5grZV3jwIzbwXc7l3IFO",
    "う": "1ozopveWMLTMCh6Q_0uihsD3EY8h33Wi2",
    "え": "1J_8BTJY286TvlMPDyc00JJjLOcUdO-F8",
    "お": "12zRNRLqYCScM3owUtbx_NdaIUWq3nxv8",
    "か": "1cpkpwUA3EKUwg3ff5dtUlhIBGQ3Ri_G6",
    "き": "150y2HczafC98V8ZFzMRdFTmxr9gBiDEs",
    "く": "148R19RHjkGAW1_v5-FUWVbAigPtpTleI",
    "け": "12WzgxO4mvRUgOjlKN4rkRw2hFFGIlfkV",
    "ご": "1EbRiYyIK3FGPWx1qU63onjKTEa-g4fYV",
    "さ": "1YFO-4r1aFkEbFd5n37P2h27P_gxivlGq",
    "し": "1eNMA7xWimCIU-7ZHvNBc-rEdpt2Nbvrs",
    "す": "1QcS1Rl5iNzc4sa6uuINDE3XJwjtA5w1N",
    "せ": "19-70aawFvx_zdoCy-_T3PwtYic-MAkgb",
    "そ": "1K6Wau-46t4BtvyJ2JmmcxeYh2QCBkKxN",
    "た": "1oD_f1Gi3XgLXM1pzpU9s84-jpyOweDQp",
    "ち": "152U6CtisRiCnY78A-HF5f-tINb_LYc3l",
    "つ": "1osc7jbJyXk0pYZjPuf-Cz-jVP7v6xV7x",
    "て": "1XdYElCzgV_LA_hH0yaQ1CadCp922K-Su",
    "と": "1YlMWEbKolZmdawNpTtLgvby9-3FSBO2_",
    "な": "19LBSd66HIvhuSvSVNfEEONI0cIGL209U",
    "に": "1fjtO7SZDFtD8osDyvUX-zP0yEYeds9OF",
    "ぬ": "1LjpZeqqcg_anMEMopzCYvcW5wc8vmge6",
    "ね": "1T6Lr5tjUASlWwLFnN54pNOrBpVr3N0vR",
    "の": "/1mMA0hXj27IXelm6CACEktCr_aGQ8lzAk",
    "は": "1p6dB2lKBs8MngdYpdk57ZHTuKWyrE0_S",
    "ひ": "1psHEgqDoNRt9mmh40a2PVR5IikZcK5xj",
    "ふ": "1pz2VJlPfHDjjHcBc-Ml0OolSD3TEDHi1",
    "へ": "13TawhJjTGHaVq8B0GNUki6RLA8gp2yvH",
    "ほ": "1rFVzOgkWSFGAsN2SGohxiAsLfgMkGvE4",
    "ま": "1snNBXy5oF0o0Xde-5VANQ6CVo_LRz3m5",
    "み": "1QNNSN5HVMjipchSNWcI3lDvIt_8YFGrC",
    "む": "1TRporMnQ92xvh4yajTbG6GDV_yVdsc1B",
    "め": "132gLQohNFoGLR7AaXRQ8BMdQh-CYu9XE",
    "も": "1fksuYLiUdylSCfD6jpRGOJFGfGcxK-IY",
    "や": "1fnPI9F4mCrrMC8K6ECpDF_77qUQsI9f9",
    "ゆ": "1jGqYQRN5xyLrBxUjV6L19mFhYr4cwB7p",
    "よ": "107NNSlo6e_ICVZggfELjyM0fWmPIQh1a",
    "ら": "1HRAQE2JKLSb65V4iYDEoIREnJRCcyBDa",
    "り": "1GkBHQW1qlCBJ-I6A5l7zdGsSU-EDXKGJ",
    "る": "12iTRAHlqa7bAstZvd3SIDx8m0UFZTvHn",
    "れ": "1m9vGxYBBRFIUXFuhifubjcP1LRPgRcgD",
    "ろ": "1708ZKi4NuJ5FqEbvPSOO0NGtaKwqNi4b",
    "わ": "1bHCK_-Dy4jgSPubuKY0bELQFRL4o0BtP",
    "を": "1obNR12X5MJ_oeYZJ22wKcyLS649k_BiY",
    "ん": "1uIye20OkRPZa1ORTTOTlLt8l-mo2oeQt",
    "が": "1SqwccSBNanU4wM1WCWBHC2fCPRO2BeKj",
    "ぎ": "1ZLmV8Cp9DCsW2mwSpafud8SxemOl3dGI",
    "ぐ": "1galHzibMoBD_1-7lol-X3v6RdgItV7va",
    "げ": "1P6gWAveVjvQYXlqP6zkX3VigLlWtBaus",
    "ご": "1AwsBODN-b3ohQTa5IXlcz7m6LuZCr7bG",
    "ざ": "13AbnN93UNaYo2p-VgjTPXFOcCXxkTxWv",
    "じ": "1Uy8l3McuZzO1S9VHz-J74xvOnWRe0wFa",
    "ず": "1P_FvoO29rCNFUVNRuhnvGpPmRIsG6HG1",
    "ぜ": "1QflPrMIsDAJ4zMBaitjxuSWZy8Fux3rx",
    "ぞ": "1Ke7vqUC9wrOgbeHQZnRe0KuI60mTOTEw",
    "だ": "15ob36UFyftU-ezXoBDqBnAFR-TcZJAdJ",
    "ぢ": "1_BXLlwznWPPGyv8RBPjEV8EWHLLoxCLv",
    "づ": "1E78D2C-c2RofmvLRJ_cVANyiFdzwg9cI",
    "で": "1Ej9-VvnuJbWaq4JLOiSrbOHKvFsoIXy_",
    "ど": "19PeLfmuH7qL6_GuMsu0CQMs60ZO7LIPp",
    "ば": "1eJFvDdvF2i13kY5W1e8KGfUJuPV8ECM5",
    "び": "1_gA_KSuCYuHqtuA3OYWjJNN4rEagmHO8",
    "ぶ": "175HFQBnnM796yVpxppc1msYxf7OrLPz4",
    "べ": "1beQ9FQSBAz8BNRi0AF1f5KQ7kJCmJ46N",
    "ぼ": "1iUa3-ZGIAK6N6gl3IBP_ytcDYyIAJMXj",
    "ぱ": "1r9MXpT9dATwF92d3Ro2Go0lXnZoQdbmy",
    "ぴ": "1gWa_ViuSQdt-I54YlvtCddKG5YCFecp5",
    "ぷ": "1gyN7Q4R6HOg47wiQC03yAvMH-UZVXv5E",
    "ぺ": "1UyJ4lY9ksuxvjWPGeCthoCz0BqMyJMDz",
    "ぽ": "1ptJwP7vQoRaKGfYPOgat4jvvD70GvRYA",
    "きゃ": "1e57n2CV5fCkKc34ONvbEd1M2brrjhwmU",
    "きゅ": "1MRRkxD5zHQs9F9oVhrHqtzUihOLSf9oY",
    "きょ": "1MRRkxD5zHQs9F9oVhrHqtzUihOLSf9oY",
    "きょ": "1i0IBUfjfwlSEUv1RQKckfL194duLrXWt",
    "しゅ": "1NgKQbeeKKlHgVgzE01pVQPYchj2qAmZC",
    "しょ": "1hEcVh2lQ03dEl5ATPrkKPfsfSXwz9xf2",
    "ちゃ": "1ZwfAypRnMdTVyc_3qNeYWZb-VhWfyxdP",
    "ちゅ": "1dMMdnyrgzEiWN-5i9CTg1ljgyeZ5Km9g",
    "ちょ": "1kBQEngw3OmSuo9MzKc2TlaKGNw6mOWBk",
    "にゃ": "1gPeJTMKvLwkxNtWWRKp_QxuI1fWW04nO",
    "にゅ": "1Dgy_P4ymNhTFJp_72VcdZNPHXvWYGTLR",
    "にょ": "1JgA1TjMsfJGC6hql0IXIthvWV1hUBdAU",
    "ひゃ": "1WqtE3CKpxt8C1UwHyamSMrqAd-PSZ2--",
    "ひゅ": "1ozTIBG3KrWuzE0h9zNhbd2_Da40VRyl3",
    "ひょ": "1yeaXAZeP_Z-CGBbxiEwDKeIKS0CopXWZ",
    "みゃ": "1wftleVz4Ix7hMpf-P5lqH9gKa_TI3m1M",
    "みゅ": "1jvUAZ-SZPrRgghFT1E8DbWvovq_5wPFX",
    "みょ": "1o9GxhW5PY7O9S7gv9pRPBkkrl0h_LqGB",
    "りゃ": "1Vsg5bkwHO5cwYQYmNqKmUnkJ4O21e1ic",
    "りゅ": "1NAfzk-UNCfFK9HP-8Mh1vZCr3-JJYjeA",
    "りょ": "1cNDGNPWTb-sKof9gZ8_uCUOA_ACJWH9e",
    "ぎゃ": "1fQfxlHNv99sLWe766Ce7zU5S1U0DHbcQ",
    "ぎゅ": "1y3rTFVQ9mOoDy4JNjeBnepGzbbhkpMmE",
    "ぎょ": "1hq45WmBWVHBZRuit6wYdgWqnex03FCEe",
    "じゃ": "1ov7ewK6oZe0Z81USn7yPm7B7JqZJd5Zs",
    "じゅ": "16WXjWe020dDBocrb_k5oXOTQxhaxU9Za",
    "じょ": "1vgrPLWRUnZBG8qFxBDe8reBbktitthXA",
    "びゃ": "1Ch2fIayAchl4PfNdIPzsQwHaWf-i1dUh",
    "びゅ": "1UDod8vJ6ae2-Fgje0T8b44SXJqCwUmX8",
    "びょ": "1VCbp8goKIHCafK6gCNigg1279fEff5W0",    
    "ぴゃ": "14g-BBfkzrwl44GG7VGrVvKw9spyMjqyr",
    "ぴゅ": "1FWC5qSuuMm6krNtk9YpjpNH8priBMmgQ",
    # … 其他假名依序填上
}
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

start = (1,1)
goal = (maze_size-2, maze_size-2)
maze[goal[0]][goal[1]] = "⛩"
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
                    "2. 我要玩迷宮遊戲\n"
                    "3. 我要玩賽車遊戲\n"
                    "4. 我要玩射飛鏢 進階篇\n"
                    "5. 我要填問卷～\n\n"
                    "【遊戲規則】\n"
                    "📘 看五十音：查看所有平假名、片假名與羅馬拼音對照。\n"
                    "🧩 迷宮遊戲：使用『上/下/左/右』移動角色，遇到假名選擇題時答對才能繼續。\n"
                    "🏎 賽車遊戲：每次輸入『前進』會推進一格，抵達終點即勝利！\n"
                    "🎯 射飛鏢遊戲：隨機射中一個日文單字（含中文意義），請選出正確的羅馬拼音，答對即命中！"
                )
                reply_text(reply_token, menu)

            elif text == "1" or text == "我要看五十音":
                reply_text(reply_token, get_kana_table())

            elif text == "2" or text == "我要玩迷宮遊戲":
                players[user_id] = {"pos": (1, 1), "quiz": None, "game": "maze", "score": 0}
                reply_text(reply_token, render_map((1, 1)) + "\n🌟 迷宮遊戲開始！請輸入「上」「下」「左」「右」移動。")

            elif text == "3" or text == "我要玩賽車遊戲":
                players[user_id] = {"car_pos": 0, "game": "race", "quiz": None, "last_quiz": None, "last_msg": None}
                reply_text(reply_token, render_race(0) + "\n🏁 賽車遊戲開始！請輸入「前進」來推進你的車子。")

            elif text == "4" or text == "我要玩射飛鏢":
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

            elif text == "5" or text == "我要填問卷～":
                reply_text(reply_token, "📋 請點選以下連結填寫問卷：\nhttps://forms.gle/w5GNDJ7PY9uWTpsG6")
            elif user_id in players and players[user_id].get("game") == "maze" and text in ["上","下","左","右"]:
                result = maze_game(user_id, text)
                if result.get("audio + text"):
                    headers = {
                        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
                        "Content-Type":    "application/json"
                    }
                    body = {
                        "replyToken": reply_token,
                        "messages": [
                            {
                                "type":               "audio",
                                "originalContentUrl": result["audio"],
                                "duration":           1500
                            },
                            {
                                "type": "text",
                                "text": result["map"] + "\n💬 " + result["message"]
                            }
                        ]
                    }
                    requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=body)
                else:
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
def maze_game(user, message):
    player = players.setdefault(user, {"pos": start, "quiz": None, "game": "maze", "score": 0})
    if player.get("quiz"):
        kana, answer, choice_map = player["quiz"]
        if message in choice_map and choice_map[message] == answer:
            player["quiz"] = None
            return {"map": render_map(player["pos"]), "message": "✅ 回答正確，繼續前進！"}
        else:
            options_text = "\n".join([f"{key}. {val}" for key, val in choice_map.items()])
            return {"map": render_map(player["pos"]), "message": f"❌ 回答錯誤，請再試一次：\n{options_text}"}
    direction = {"上": (-1, 0), "下": (1, 0), "左": (0, -1), "右": (0, 1)}
    if message not in direction:
        return {"map": render_map(player["pos"]), "message": "請輸入方向：上、下、左、右"}
    dy, dx = direction[message]
    y, x = player["pos"]
    new_pos = (y + dy, x + dx)
    if not (0 <= new_pos[0] < maze_size and 0 <= new_pos[1] < maze_size) or maze[new_pos[0]][new_pos[1]] == "⬛":
        return {"map": render_map(player["pos"]), "message": "🚧 前方是牆，不能走喔！"}
    player["pos"] = new_pos
    if new_pos == (2, 5):
        player["pos"] = goal
        return {"map": render_map(goal), "message": "🎁 幸運！你搭上瞬移傳送門，直達終點！"}
    if new_pos == goal:
        players.pop(user)
        return {"map": render_map(new_pos), "message": "🎉 恭喜你到達終點！遊戲完成！輸入 '主選單' 重新開始"}
    if new_pos in quiz_positions or random.random() < 0.5:
        # 隨機挑假名
        kana, correct = random.choice(list(kana_dict.items()))

        # 產生三個選項
        options = [correct]
        while len(options) < 3:
            distractor = random.choice(list(kana_dict.values()))
            if distractor not in options:
                options.append(distractor)
        random.shuffle(options)
        choice_map = {"A": options[0], "B": options[1], "C": options[2]}

        # 選項文字
        options_text = "\n".join([f"{k}. {v}" for k, v in choice_map.items()])

        # Google Drive 下載直鏈
        file_id   = drive_id_map.get(kana)
        audio_url = f"https://drive.google.com/uc?export=download&id={file_id}"

        return {
            "map":     render_map(new_pos),
            "message": f"❓ 挑戰：「{kana}」的羅馬拼音是？\n{options_text}",
            "audio":   audio_url
        }
    return {"map": render_map(new_pos), "message": f"你移動了，可以繼續前進（得分 {player.get('score', 0)} 分）"}
    # 🧩 迷宮遊戲邏輯

def maze_game(user, message):
    player = players.setdefault(user, {"pos": start, "quiz": None, "game": "maze", "score": 0})

    # 如果有待回答的題目，就處理答案（答案應為 A, B, C 形式）
    if player.get("quiz"):
        kana, answer, choice_map = player["quiz"]
        if message in choice_map and choice_map[message] == answer:
            player["quiz"] = None
            return {"map": render_map(player["pos"]), "message": "✅ 回答正確，繼續前進！"}
        else:
            options_text = "\n".join([f"{key}. {val}" for key, val in choice_map.items()])
            return {"map": render_map(player["pos"]), "message": f"❌ 回答錯誤，請再試一次：\n{options_text}"}

    # 否則處理移動
    direction = {"上": (-1, 0), "下": (1, 0), "左": (0, -1), "右": (0, 1)}
    if message not in direction:
        return {"map": render_map(player["pos"]), "message": "請輸入方向：上、下、左、右"}
        
    dy, dx = direction[message]
    y, x = player["pos"]
    new_pos = (y + dy, x + dx)

    if not (0 <= new_pos[0] < maze_size and 0 <= new_pos[1] < maze_size) or maze[new_pos[0]][new_pos[1]] == "⬛":
        return {"map": render_map(player["pos"]), "message": "🚧 前方是牆，不能走喔！"}

    player["pos"] = new_pos

    # 若到特定格子（例：(2,5)）則瞬移至終點
    if new_pos == (2, 5):
        player["pos"] = goal
        return {"map": render_map(goal), "message": "🎁 幸運！你搭上瞬移傳送門，直達終點！"}

    if new_pos == goal:
        players.pop(user)
        return {"map": render_map(new_pos), "message": "🎉 恭喜你到達終點！遊戲完成！輸入 '主選單' 重新開始"}

    # 出題：若移動到題目格 或 隨機觸發題目
    if new_pos in quiz_positions or random.random() < 0.5:
        kana, correct = random.choice(list(kana_dict.items()))
        options = [correct]
        while len(options) < 3:
            distractor = random.choice(list(kana_dict.values()))
            if distractor not in options:
                options.append(distractor)
        random.shuffle(options)
        choice_map = {"A": options[0], "B": options[1], "C": options[2]}
        player["quiz"] = (kana, correct, choice_map)
        player["score"] = player.get("score", 0) + 1
        options_text = "\n".join([f"{key}. {val}" for key, val in choice_map.items()])
        return {"map": render_map(new_pos), "message": f"❓ 挑戰：「{kana}」的羅馬拼音是？\n請從下列選項點選：\n{options_text}"}
        
    return {"map": render_map(new_pos), "message": f"你移動了，可以繼續前進（得分 {player.get('score', 0)} 分）"}


# 🧩 顯示迷宮地圖

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

# 新增一個賽車遊戲的回答處理函式
def race_answer(user, answer):
    player = players.get(user)
    if not player or not player.get("last_quiz"):
        return "沒有待回答的題目，請輸入『前進』以獲得新題目。"
    kana, correct, choice_map = player["last_quiz"]
    if answer in choice_map and choice_map[answer] == correct:
        player["car_pos"] += 1
        # 清除 quiz 和 last_quiz，使每次「前進」會產生新題目
        player["quiz"] = None
        player["last_quiz"] = None
        return render_race(player["car_pos"]) + "\n✅ 回答正確，請輸入『前進』以獲得新題目！"
    else:
        return render_race(player["car_pos"], kana, choice_map) + "\n❌ 回答錯誤，請再試一次！"
# 🏎 賽車遊戲畫面顯示

def render_race(pos, kana=None, options=None):
    track = ["⬜" for _ in range(10)]
    if pos >= len(track):
        return "🏁 你贏了！賽車抵達終點！\n輸入 '主選單' 重新開始"
    track[pos] = "🏎"
    race_line = "🚗 賽車進度：\n" + ''.join(track)
    if kana and options:
        options_text = "\n".join([f"{key}. {val}" for key, val in options.items()])
        return f"{race_line}\n\n❓ 請問「{kana}」的羅馬拼音是？\n{options_text}\n請按按鈕作答（A/B/C）。"
    return race_line

# 🏎 賽車遊戲回答處理
def race_answer(user, answer):
    player = players.get(user)
    if not player or not player.get("last_quiz"):
        return "沒有待回答的題目，請輸入『前進』以獲得新題目。"
    kana, correct, choice_map = player["last_quiz"]
    if answer in choice_map and choice_map[answer] == correct:
        player["car_pos"] += 1
        player["quiz"] = None
        player["last_quiz"] = None
        return render_race(player["car_pos"]) + "\n✅ 回答正確，請輸入『前進』以獲得新題目！"
    else:
        return render_race(player["car_pos"], kana, choice_map) + "\n❌ 回答錯誤，請再試一次！"

# 🏎 賽車遊戲畫面顯示
def render_race(pos, kana=None, options=None):
    track = ["⬜" for _ in range(10)]
    if pos >= len(track):
        return "🏁 你贏了！賽車抵達終點！\n輸入 '主選單' 重新開始"
    track[pos] = "🏎"
    race_line = "🚗 賽車進度：\n" + ''.join(track)
    if kana and options:
        options_text = "\n".join([f"{key}. {val}" for key, val in options.items()])
        return f"{race_line}\n\n❓ 請問「{kana}」的羅馬拼音是？\n{options_text}\n請按按鈕作答（A/B/C）。"
    return race_line

# 🏎 賽車遊戲邏輯
def race_game(user):
    if user not in players:
        players[user] = {"car_pos": 0, "game": "race", "quiz": None}
    player = players[user]
    if player.get("quiz"):
        kana, correct, choice_map = player["quiz"]
        player["last_quiz"] = (kana, correct, choice_map)
        return render_race(player["car_pos"], kana, choice_map)
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
