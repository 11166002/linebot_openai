from flask import Flask, request, jsonify, abort
import os
from google.cloud import vision
import io

# === LINE 套件
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *

# === 設定 Google OCR 金鑰（請先放好 credentials.json）
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"

# === 初始化 Flask App
app = Flask(__name__)
UPLOAD_FOLDER = 'static'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# === LINE Bot 金鑰（請填入你自己的）
LINE_CHANNEL_ACCESS_TOKEN = 'liqx01baPcbWbRF5if7oqBsZyf2+2L0eTOwvbIJ6f2Wec6is4sVd5onjl4fQAmc4n8EuqMfo7prlaG5la6kXb/y1gWOnk8ztwjjx2ZnukQbPJQeDwwcPEdFTOGOmQ1t88bQLvgQVczlzc/S9Q/6y5gdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = 'cd9fbd2ce22b12f243c5fcd2d97e5680'
LIFF_URL = 'Ue86fae922eab052ddd27459b242474c0'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# === OCR 辨識函式
def detect_text(path):
    client = vision.ImageAnnotatorClient()
    with io.open(path, 'rb') as f:
        content = f.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    return texts[0].description.strip() if texts else "👀 沒看到假名耶，再寫一次吧！"

# === 圖片上傳用路由（供 LIFF 用）
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': '😿 你還沒上傳圖片喔！'}), 400

    f = request.files['image']
    path = os.path.join(UPLOAD_FOLDER, 'input.png')
    f.save(path)

    result = detect_text(path)
    return jsonify({
        'recognized_text': f"🎌【Japan Learning Game】判定你寫的是：「{result}」！🌟",
        'note': "📣 如果不是你想寫的，再來一次也沒關係喔，加油！"
    })

# === LINE Webhook 路由
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# === 處理 LINE 訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text

    if text == "我要練習":
        message = TemplateSendMessage(
            alt_text="來練習寫假名吧！",
            template=ButtonsTemplate(
                title="日文假名練習",
                text="點擊進入 Japan Learning Game 畫圖上傳畫面",
                actions=[URIAction(label="開始練習", uri=LIFF_URL)]
            )
        )
        line_bot_api.reply_message(event.reply_token, message)
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="輸入「我要練習」來開始唷 ✍️"))

# === 預設首頁
@app.route('/')
def home():
    return '👋 Welcome to Japan Learning Game OCR + LINE Bot Server 🎌！'

# === 啟動 Flask 應用
if __name__ == '__main__':
    app.run(debug=True)
