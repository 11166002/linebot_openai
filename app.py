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

# 填字遊戲題庫 (以羅馬拼音為答案)
crossword = {
    "mizu": {"hint": "日語的「水」羅馬拼音", "filled": False},
    "kuruma": {"hint": "日語的「車」羅馬拼音", "filled": False},
    "taberu": {"hint": "日語的「吃」羅馬拼音", "filled": False},
}

# 存放每位使用者的遊戲進度
user_progress = {}

# 棋盤格狀態
def generate_board(progress):
    board = "填字棋盤:\n"
    for word, info in crossword.items():
        status = "✅" if progress[word] else "⬜"
        board += f"{info['hint']} [{status}]\n"
    return board

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_input = event.message.text.strip().lower()

    if user_id not in user_progress:
        user_progress[user_id] = {word: False for word in crossword}

    if user_input == "開始遊戲":
        hints = "\n".join([f"• {v['hint']}" for k, v in crossword.items()])
        board = generate_board(user_progress[user_id])
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"🧩填字遊戲開始！\n題目提示:\n{hints}\n{board}\n請輸入答案！")
        )
        return

    if user_input in crossword:
        if user_progress[user_id][user_input]:
            reply = "你已經答過這個字囉，請輸入其他答案！"
        else:
            user_progress[user_id][user_input] = True
            reply = f"✅「{user_input}」正確！"
    else:
        reply = "❌錯誤答案，請再試一次！"

    # 檢查是否完成所有題目
    if all(user_progress[user_id].values()):
        reply += "\n🎉恭喜完成所有題目！輸入「開始遊戲」重新挑戰！"
        user_progress.pop(user_id)
    else:
        reply += "\n" + generate_board(user_progress[user_id])

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    app.run(debug=True)
