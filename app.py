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
    user_message = event.message.text.strip()  # 使用 strip() 方法去除首尾空白字符
# 预处理和验证
if not user_message:
    return send_error_message(event, "输入内容不能为空，请重新输入。")

if len(user_message) > 2000:
    return send_error_message(event, "输入内容过长，请简化后再试。")

if detected_lang == 'zh-cn' or detected_lang == 'zh-tw':
    return send_error_message(event, "请输入其他语言内容以进行翻译。")
    # 使用Groq API进行翻译
    prompt = f"请将以下文本翻译为中文'{user_message}'"
    completion = groq_client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {
                "role": "system", 
                "content": (
                    "你是一个专业的翻译助手。你的任务是将用户的输入准确、流畅地翻译成地道的中文。"
                    "保持原文的意思和语气，但要确保翻译听起来自然、符合中文表达习惯。"
                    "处理规则："
                    "1. 如果用户的输入是中文，返回提示消息：'请输入其他语言内容以进行翻译。'。"
                    "2. 如果用户的输入为空或无效，返回提示消息：'输入内容不能为空或无效，请重新输入。'。"
                    "3. 如果输入内容过长（超过2000字符），返回提示消息：'输入内容过长，请简化后再试。'。"
                    "4. 如果用户输入包含特殊字符、标签符号等，返回提示消息：'请只输入文字内容进行翻译。'。"
                    "5. 对于敏感或不适宜的内容，返回提示消息：'输入内容包含敏感信息，无法翻译。'。"
                    "只返回翻译内容，不要附加任何说明或笔记。"
                )
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