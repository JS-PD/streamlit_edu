import streamlit as st
import tiktoken
from loguru import logger

from langchain.chains import ConversationalRetrievalChain
from langchain_community.chat_models import ChatOpenAI

from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.document_loaders import UnstructuredExcelLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import Docx2txtLoader
from langchain_community.document_loaders import UnstructuredPowerPointLoader

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings

from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores import FAISS

# from streamlit_chat import message
from langchain_community.callbacks import get_openai_callback
from langchain.memory import StreamlitChatMessageHistory

import time

from st_aggrid import AgGrid
import pandas as pd

import requests
import json

import bs4
from bs4 import BeautifulSoup
from langchain_community.document_loaders import WebBaseLoader       

from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

import os
import base64
import re
from dotenv import load_dotenv

# API 키 정보 로드
load_dotenv()

def main():
    st.set_page_config(
    page_title="DirChat",
    page_icon=":books:")

    #st.title("_Private Data :red[QA Chat]_ :books:")
    st.title("테스트 챗봇(RAG)")
        
    if "conversation" not in st.session_state:
        st.session_state.conversation = None

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    if "processComplete" not in st.session_state:
        st.session_state.processComplete = None

    with st.sidebar:
        uploaded_files =  st.file_uploader("Upload your file",type=['pdf','docx','pptx','txt','csv','xlsx'],accept_multiple_files=True)

        openai_api_key = st.text_input("OpenAI API Key", st.secrets['OPENAI_API_KEY']['OPENAI_API_KEY'], key="chatbot_api_key", type="password", )

        process = st.button("Process")
        
        data_api_key = st.text_input("DATA.GO.KR API Key", st.secrets[DATA_API_KEY][DATA_API_KEY], key="data_api_key", type="password")

        get_username = st.text_input("Insta username", st.secrets[username][username], key="get_username", type="default")

        get_password = st.text_input("Insta password", st.secrets[password][password], key="get_password", type="password")



        get_word = st.text_input('검색할 #태그를 입력하세요', placeholder='ex)스마트팜')
        get_insta = st.button("Get Instagram")

        get_api = st.button("get_api")

        get_url = st.text_input('검색할 기사의 URL를 입력하세요', 'https://www.aflnews.co.kr/news/articleView.html?idxno=267041', placeholder='ex)https://www.aflnews.co.kr/news/articleView.html?idxno=267041')
        get_news = st.button("get_news")

        get_data = st.button("get_data")
        
    if get_insta:
        if not openai_api_key:
            st.info("Open AI에서 발급받은 키를 입력해주세요")
            st.stop()
        if not get_word:
            warning_message = st.sidebar.warning('검색할 #태그를 입력하세요', icon="⚠️")
            time.sleep(2)
            warning_message.empty()
            st.stop()
        if not get_username:
            st.info("ID를 입력해주세요")
            st.stop()
        if not get_password:
            st.info("패스워드를 입력해주세요")
            st.stop()
        else:   
            import get_insta_hashtag
            get_insta_hashtag.main(get_word, get_username, get_password)

            warning_message = st.sidebar.warning('수집 된 데이터를 처리하고 있습니다', icon="⚠️")
            
            df = pd.read_excel('insta_crawling.xlsx')
            AgGrid(df)

            doc_list = []
            loader = UnstructuredExcelLoader("insta_crawling.xlsx")
            documents = loader.load_and_split()
            doc_list.extend(documents)
            
            text_chunks = get_text_chunks(doc_list)
            vetorestore = get_vectorstore(text_chunks)
        
            st.session_state.conversation = get_conversation_chain(vetorestore,openai_api_key) 

            st.session_state.processComplete = True

            warning_message.empty()
            warning_message = st.sidebar.warning('데이터 처리가 완료었습니다', icon="⚠️")


    if get_news:
        if not openai_api_key:
            st.info("Open AI에서 발급받은 키를 입력해주세요")
            st.stop()
        if not get_url:
            warning_message = st.sidebar.warning('검색할 URL을 입력하세요', icon="⚠️")
            time.sleep(2)
            warning_message.empty()

        else:   
            warning_message = st.sidebar.warning('수집 된 데이터를 처리하고 있습니다', icon="⚠️") 

            url = get_url

            response_header = requests.get(url)
            soup = BeautifulSoup(response_header.text, 'html.parser') 

            program_names = soup.select('.powerful-con .flex-start in-num')
            
            program_names = soup.select_one('.heading').get_text()

            with st.chat_message("user"):
                st.markdown(f"#### 추출 기사 : {program_names}")

            loader = WebBaseLoader(
                web_paths=(url,),
                bs_kwargs=dict(
                    parse_only=bs4.SoupStrainer(
                        "article",
                        attrs={"class": ["grid body"]},
                    )
                ),
            )

            doc_list = []

            documents = loader.load_and_split()
            doc_list.extend(documents)
            
            text_chunks = get_text_chunks(doc_list)
            vetorestore = get_vectorstore(text_chunks)
        
            st.session_state.conversation = get_conversation_chain(vetorestore,openai_api_key) 

            st.session_state.processComplete = True

            warning_message.empty()
            warning_message = st.sidebar.warning('데이터 처리가 완료었습니다', icon="⚠️")

    if get_data:
        if not openai_api_key:
            st.info("Open AI에서 발급받은 키를 입력해주세요")
            st.stop()
        url = "https://scienceon.kisti.re.kr/aiq/mlsh3/selectAIQMlshList.do"

        response_header = requests.get(url)
        soup = BeautifulSoup(response_header.text, 'html.parser') 

        for i in range(0,5):
            title = soup.select(".subject")[i].text.replace("	", "").replace("\n", "")
            writer_temp = soup.select_one("#art_author_" + str(i))
            writer = writer_temp.text.replace("	", "").replace("\n", "")
            st.write(f"#### {title}")
            st.write(f"```{writer}```\n")
            
        warning_message = st.sidebar.warning('수집 된 데이터를 처리하고 있습니다', icon="⚠️")

        loader = WebBaseLoader(
            web_paths=(url,),
            bs_kwargs=dict(
                parse_only=bs4.SoupStrainer(
                    "div",
                    attrs={"class": ["powerful-con flex-start in-num"]},
                )
            ),
        )

        doc_list = []
        
        documents = loader.load_and_split()
        doc_list.extend(documents)
        
        text_chunks = get_text_chunks(doc_list)
        vetorestore = get_vectorstore(text_chunks)
    
        st.session_state.conversation = get_conversation_chain(vetorestore,openai_api_key) 

        st.session_state.processComplete = True

        warning_message.empty()
        warning_message = st.sidebar.warning('데이터 처리가 완료었습니다', icon="⚠️")

    if process:
        if not openai_api_key:
            st.info("Open AI에서 발급받은 키를 입력해주세요")
            st.stop()
        files_text = get_text(uploaded_files)
        text_chunks = get_text_chunks(files_text)
        vetorestore = get_vectorstore(text_chunks)
     
        st.session_state.conversation = get_conversation_chain(vetorestore,openai_api_key) 

        st.session_state.processComplete = True

    if get_api:
        if not data_api_key:
            st.info("공공데이터 포럼에서 발급받은 키를 입력해주세요")
            st.stop()
        if not openai_api_key:
            st.info("Open AI에서 발급받은 키를 입력해주세요")
            st.stop()
        warning_message = st.sidebar.warning('수집 된 데이터를 처리하고 있습니다', icon="⚠️")

        url = 'http://apis.data.go.kr/1230000/BidPublicInfoService04/getBidPblancListInfoThngPPSSrch01?'
        params ={'serviceKey' : data_api_key
                , 'numOfRows' : '10', 'pageNo' : '1', 'inqryDiv' : '1', 'indstrytyCd' : '1244', 'inqryBgnDt' : '202402110000', 'inqryEndDt' : '202403120000', 'type' : 'json' }

        response = requests.get(url, params=params)
        content = response.text

        json_object = json.loads(content)

        body = json_object['response']['body']['items']

        df = pd.json_normalize(body)

        df.to_excel('data_api_result.xlsx')

        st_df = pd.DataFrame(data={
            '입찰공고명':[df['rgstTyNm'][0],df['rgstTyNm'][1],df['rgstTyNm'][2]],
            '품목명':[df['bidNtceNm'][0],df['bidNtceNm'][1],df['bidNtceNm'][2]],
            '담당자':[df['ntceInsttOfclNm'][0],df['ntceInsttOfclNm'][1],df['ntceInsttOfclNm'][2]]
        })
        st.dataframe(st_df)
        
        doc_list = []
        loader = UnstructuredExcelLoader("data_api_result.xlsx")
        documents = loader.load_and_split()
        doc_list.extend(documents)
        
        text_chunks = get_text_chunks(doc_list)
        vetorestore = get_vectorstore(text_chunks)
    
        st.session_state.conversation = get_conversation_chain(vetorestore,openai_api_key) 

        st.session_state.processComplete = True

        warning_message.empty()
        warning_message = st.sidebar.warning('데이터 처리가 완료었습니다', icon="⚠️")

    if 'messages' not in st.session_state:
        st.session_state['messages'] = [{"role": "assistant", 
                                        "content": "ko-sroberta-multitask + gpt-3.5-turbo"}]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    history = StreamlitChatMessageHistory(key="chat_messages")

    # Chat logic
    if query := st.chat_input("질문을 입력해주세요."):
        st.session_state.messages.append({"role": "user", "content": query})

        with st.chat_message("user"):
            st.markdown(query)

        with st.chat_message("assistant"):
            chain = st.session_state.conversation

            with st.spinner("Thinking..."):
                result = chain({"question": query})
                with get_openai_callback() as cb:
                    st.session_state.chat_history = result['chat_history']
                response = result['answer']
                print(response)
                source_documents = result['source_documents']

                st.markdown(response)
                
                with st.expander("참고 문서 확인"):
                    st.markdown(source_documents[0].metadata['source'], help = source_documents[0].page_content)
                    st.markdown(source_documents[1].metadata['source'], help = source_documents[1].page_content)
                    st.markdown(source_documents[2].metadata['source'], help = source_documents[2].page_content)
                    


# Add assistant message to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})


def tiktoken_len(text):
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokens = tokenizer.encode(text)
    return len(tokens)

def get_text(docs):

    doc_list = []
    
    for doc in docs:
        file_name = doc.name  # doc 객체의 이름을 파일 이름으로 사용
        with open(file_name, "wb") as file:  # 파일을 doc.name으로 저장
            file.write(doc.getvalue())
            logger.info(f"Uploaded {file_name}")
        if '.pdf' in doc.name:
            loader = PyPDFLoader(file_name)
            documents = loader.load_and_split()
        elif '.docx' in doc.name:
            loader = Docx2txtLoader(file_name)
            documents = loader.load_and_split()
        elif '.pptx' in doc.name:
            loader = UnstructuredPowerPointLoader(file_name)
            documents = loader.load_and_split()
        elif '.txt' in doc.name:
            loader = TextLoader(file_name, encoding = 'UTF-8')
            documents = loader.load_and_split()
        elif '.csv' in doc.name:
            loader = CSVLoader(file_name)
            documents = loader.load_and_split()
        elif '.xlsx' in doc.name:
            loader = UnstructuredExcelLoader(file_name)
            documents = loader.load_and_split()

        doc_list.extend(documents)
    return doc_list


def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=100,
        length_function=tiktoken_len
    )
    chunks = text_splitter.split_documents(text)
    return chunks


def get_vectorstore(text_chunks):
    embeddings = HuggingFaceEmbeddings(
                                        model_name="jhgan/ko-sroberta-multitask",
                                        model_kwargs={'device': 'cpu'},
                                        encode_kwargs={'normalize_embeddings': True}
                                        )  
    vectordb = FAISS.from_documents(text_chunks, embeddings)
    return vectordb

def get_conversation_chain(vetorestore,openai_api_key):
    llm = ChatOpenAI(openai_api_key=openai_api_key, model_name = 'gpt-4o',temperature=0)
    
    conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=llm, 
            chain_type="stuff", 
            retriever=vetorestore.as_retriever(search_type = 'mmr', vervose = True), 
            memory=ConversationBufferMemory(memory_key='chat_history', return_messages=True, output_key='answer'),
            get_chat_history=lambda h: h,
            return_source_documents=True,
            verbose = True
        )

    return conversation_chain

if __name__ == '__main__':
    main()
