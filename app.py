import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# LINE Bot配置
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# Groq API配置
groq_client = groq.Client(api_key=os.getenv('GROQ_API_KEY'))

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
    user_message = event.message.text
    
    # 使用Groq API进行翻译
    prompt = f"翻译为中文: '{user_message}'"
    completion = groq_client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "你是一个专业的翻译助手。你的任务是将用户的输入准确、流畅地翻译成地道的中文。保持原文的意思和语气，但要确保翻译听起来自然、符合中文表达习惯。"},
            {"role": "user", "content": prompt}
        ]
    )
    translated_text = completion.choices[0].message.content

    # 发送翻译结果回LINE
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=translated_text)
    )

if __name__ == "__main__":
    app.run()