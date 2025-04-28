from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
)

app = Flask(__name__)

# 替換為你的LINE頻道資訊
line_bot_api = LineBotApi('liqx01baPcbWbRF5if7oqBsZyf2+2L0eTOwvbIJ6f2Wec6is4sVd5onjl4fQAmc4n8EuqMfo7prlaG5la6kXb/y1gWOnk8ztwjjx2ZnukQbPJQeDwwcPEdFTOGOmQ1t88bQLvgQVczlzc/S9Q/6y5gdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('cd9fbd2ce22b12f243c5fcd2d97e5680')

crossword = {
    "mizu": {"hint": "水", "filled": False, "positions": [(1,1), (2,1), (3,1), (4,1)]},
    "kuruma": {"hint": "車", "filled": False, "positions": [(1,1), (1,2), (1,3), (1,4), (1,5), (1,6)]},
    "taberu": {"hint": "吃", "filled": False, "positions": [(3,3), (3,4), (3,5), (3,6), (3,7), (3,8)]},
}

user_progress = {}

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

def generate_board(progress):
    # 初始化5x5示範棋盤
    board = [["🔲" for _ in range(5)] for _ in range(5)]

    for word, data in crossword.items():
        if progress[word]:
            for idx, (row, col) in enumerate(data["positions"]):
                board[row-1][col-1] = word[idx]

    return "\n".join("".join(row) for row in board)

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_input = event.message.text.lower().strip()

    if user_id not in user_progress:
        user_progress[user_id] = {k: False for k in crossword}

    if user_input == "開始遊戲":
        board_visual = generate_board(user_progress[user_id])
        flex_message = FlexSendMessage(
            alt_text="填字遊戲開始",
            contents={
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "🎌 日文填字遊戲", "weight": "bold", "size": "lg"},
                        {"type": "text", "text": board_visual},
                        {"type": "separator", "margin": "md"},
                        {"type": "text", "text": "🔸提示：\n1橫向：水\n2縱向：車\n3橫向：吃", "size": "sm"}
                    ]
                }
            }
        )
        line_bot_api.reply_message(event.reply_token, flex_message)
        return

    if user_input in crossword:
        if user_progress[user_id][user_input]:
            reply = "你已經答過這個詞了！"
        else:
            user_progress[user_id][user_input] = True
            reply = f"✅ 「{user_input}」正確！"
    else:
        reply = "❌ 錯誤答案，請再試一次！"

    if all(user_progress[user_id].values()):
        reply += "\n🎉 恭喜！你完成所有題目！"
        user_progress.pop(user_id)

    board_visual = generate_board(user_progress.get(user_id, {k:False for k in crossword}))
    flex_message = FlexSendMessage(
        alt_text="填字遊戲更新",
        contents={
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": reply, "weight": "bold", "size": "md"},
                    {"type": "separator", "margin": "md"},
                    {"type": "text", "text": board_visual},
                ]
            }
        }
    )

    line_bot_api.reply_message(event.reply_token, flex_message)

if __name__ == "__main__":
    app.run(debug=True)
