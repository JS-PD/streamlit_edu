from openai import OpenAI
import streamlit as st

OPENAI_API_KEY = "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"

client = OpenAI(
    api_key = OPENAI_API_KEY,
)

import speech_recognition as sr
from gtts import gTTS
import os
import playsound
from translate import Translator

def speak(text):
    tts = gTTS(text=text, lang='ko')
    filename='voice.mp3'
    tts.save(filename) # 파일을 만들고,
    playsound.playsound(filename) # 해당 음성파일을 실행(즉, 음성을 말함)
    os.remove(filename)

def speak2(text):
    tts = gTTS(text=text, lang='en')
    filename='voice.mp3'
    tts.save(filename) # 파일을 만들고,
    playsound.playsound(filename) # 해당 음성파일을 실행(즉, 음성을 말함)
    os.remove(filename)


def get_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("say something")
        audio = r.listen(source)
        said = " "

        try:
            said = r.recognize_google(audio, language="ko-KR")
            print("Your speech thinks like: ", said)
            st.session_state.messages.append({"role": "user", "content": said})
            with st.chat_message("user"):
                st.write(said)

        except Exception as e:
            print("Exception: " + str(e))
    
    return said

    
#speak("안녕하세요. 2초 후에 한국어로 말을 하시면 영어로 번역하여 말을합니다.") 


st.set_page_config(page_title="DataFrame Demo", page_icon="📊")

st.markdown("# ChatGPT Demo")
st.sidebar.header("ChatGPT Demo")
st.write(
    """This demo shows how to use `st.write` to visualize Pandas DataFrames."""
)

mic = st.button("mic")

if mic:
    get_audio()

# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])


# User-provided prompt
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

completion = client.chat.completions.create(
    #model="gpt-3.5-turbo-16k",
    model="gpt-3.5-turbo",
    stream=True,
    messages=st.session_state.messages
    )

import time

final_answer = []
# Generate a new response if last message is not from assistant
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            for chunk in completion:
                # chunk 를 저장
                chunk_content = chunk.choices[0].delta.content
                # chunk 가 문자열이면 final_answer 에 추가
                if isinstance(chunk_content, str):
                    final_answer.append(chunk_content)
                    # 토큰 단위로 실시간 답변 출력


        placeholder = st.empty()
        full_response = ''
        for item in final_answer:
            full_response += item
            placeholder.markdown(full_response)
            time.sleep(0.02)
    message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(message)