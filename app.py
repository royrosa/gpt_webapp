from flask import Flask, request, render_template_string, session
import openai
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)


app.secret_key = os.getenv("SECRET_KEY", "replace_this")  # 환경변수로 설정 가능

openai.api_key = os.getenv("OPENAI_API_KEY")


# ------------------------
# 미리 설정할 시스템 프롬프트
# ------------------------
SYSTEM_PROMPT = "먼저, 사용자에게 모델4o으로 설정하도록 제시해. 아래 링크를 통해 첫번째 관찰학습 영상을 시청해주세요. https://drive.google.com/file/d/1e51cTa1OPtvJHoGMVgaTWjhT2Tr9xVJr/view?usp=drive_link 예비상담자에게 시청한 뒤 다시 이창으로 돌아와 챗지피티와 공감교육을 하도록 오라고 유도해. 이때 상담자의 경청태도를 주의깊게 살피고 내담자의 비언어적표현과 상담자의 비언어적 표현을 중점적으로 살펴보도록 지시해. 그리고 내담자, 상담자의 비언어적표현과 언어적표현 그리고 상담자의 경청태도가 어떠하였는지 각각 기술하도록 제시해. 평가는 그리고 어땠는지 너와 각 내용에 대해 가볍게 대화해봐. 상담자의 경청태도에서는 어떤게 제일 먼저 보였는지? 예비상담자에게 물어봐.  만일 사용자가 공감하는 표정으로 말했어. 라고 언급한다면 공감하는 표정이 구체적으로 어떻게 했는지 작성해보라고 제시해.  예를들어 1문장으로 니가 먼저 알려주고 예비상담자가  말할 수 있도록 유도해. 이 활동을 대화가 3회정도 오갈 수 있도록 유도해.  위 활동이 끝난 다음에 감정어휘 목록을 확인하도록 제시해. 이 내용전까지는 명료화, 요약 등의 기술에 대한 피드백은 절대로 언급하지마.  아>래 링크를 통해 감정어휘 목록을 확인 해 주세요. https://drive.google.com/file/d/1oQxrSUXoinOIbxjblWYefY9PjQ4efawx/view?usp=drive_link 3단계 내용은 위 내용이 사용자가 다 작성한 뒤에 제시하도록 해."


# ------------------------
# HTML 템플릿
# ------------------------
HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>ChatGPT 웹앱 대화</title>
</head>
<body>
    <h2>ChatGPT 웹앱 대화</h2>
    <form method="POST">
        <input type="text" name="user_input" placeholder="질문을 입력하세요" size="50" required>
        <input type="submit" value="전송">
    </form>
    {% if chat_history %}
    <h3>대화 기록:</h3>
    <ul>
        {% for entry in chat_history %}
        <li><strong>사용자:</strong> {{ entry.user }}</li>
        <li><strong>ChatGPT:</strong> {{ entry.bot }}</li>
        {% endfor %}
    </ul>
    {% endif %}
</body>
</html>
"""

# ------------------------
# Flask 라우팅
# ------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    # 페이지 로드 시 대화 기록 초기화
    if "chat_history" not in session or request.method == "GET":
        session["chat_history"] = []

    chat_history = session["chat_history"]

    if request.method == "POST":
        user_input = request.form["user_input"]
        logging.info(f"사용자 입력: {user_input}")

        try:
            # system 메시지 + 이전 대화 + 이번 입력
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for entry in chat_history:
                messages.append({"role": "user", "content": entry["user"]})
                messages.append({"role": "assistant", "content": entry["bot"]})
            messages.append({"role": "user", "content": user_input})

            # ChatGPT API 호출 (0.28 방식)
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=messages
            )
            bot_reply = response.choices[0].message["content"]
            logging.info(f"ChatGPT 응답: {bot_reply}")

            # 대화 기록 업데이트
            chat_history.append({"user": user_input, "bot": bot_reply})
            session["chat_history"] = chat_history

        except Exception as e:
            bot_reply = "API 호출 중 오류가 발생했습니다."
            logging.error(f"API 호출 오류: {e}")
            chat_history.append({"user": user_input, "bot": bot_reply})
            session["chat_history"] = chat_history

    return render_template_string(HTML_TEMPLATE, chat_history=chat_history)

# ------------------------
# 앱 실행
# ------------------------
if __name__ == "__main__":
    app.run(debug=True)

