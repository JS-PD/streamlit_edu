from openai import OpenAI
import streamlit as st

st.set_page_config(page_title="DataFrame Demo", page_icon="📊")

st.markdown("# ChatGPT Demo")
st.sidebar.header("ChatGPT Demo")
st.write(
    """This demo shows how to use `st.write` to visualize Pandas DataFrames."""
)
with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", st.secrets['OPENAI_API_KEY']['OPENAI_API_KEY'], key="chatbot_api_key", type="password", )


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


if openai_api_key:
    client = OpenAI(
        api_key = openai_api_key,
    )

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
