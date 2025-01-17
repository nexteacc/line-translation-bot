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

@app.route("/")
def home():
    return "Hello, this is the home page!"

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Check your channel access token/channel secret.")
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    # 使用Groq API进行翻译
    prompt = f"请将以下文本翻译为中文'{user_message}'"
    completion = groq_client.chat.completions.create(
        model="mixtral-8x7b-32768",
        max_tokens=8192,
        temperature=0.2,
        messages=[
            {
                "role": "system", 
                "content": 
                    "你是一个专业的翻译助手。你的任务是将用户的输入准确、流畅地翻译成地道的中文。 保持原文的意思和语气，但要确保翻译听起来自然、符合中文表达习惯。处理规则：1. 如果用户的输入是中文，返回提示消息：'请输入其他语言内容以进行翻译'。 2. 如果用户的输入为空或无效，返回提示消息：'输入内容不能为空或无效，请重新输入'。只返回翻译内容，不要附加任何说明或笔记。"
            },
            {
                "role": "user", 
                "content": prompt
            }
        ]
    )
    translated_text = completion.choices[0].message.content

    # 发送翻译结果回LINE
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=translated_text)
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)