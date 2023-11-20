import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceInstructEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from htmlTemplet import css, bot_template, user_template
from langchain.llms import huggingface_hub
import os
import re
load_dotenv()
openai_api_key = os.getenv("open_api_key")


def get_pdf_text(pdf_docs):
    text = ''
    try:
        for pdf in pdf_docs:
            pdf_reader = PdfReader(pdf)
            for page in pdf_reader.pages:
                text += page.extract_text()
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None
    return text

def get_text_chunks(row_text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(row_text)
    return chunks

def get_vector_store(text_chunks):
    embedder = OpenAIEmbeddings(openai_api_key=openai_api_key)
    #embeddings = HuggingFaceInstructEmbeddings(model_name='hkunlp/instructor-xl')
    vactostore = FAISS.from_texts(texts=text_chunks, embedding=embedder)  
    return vactostore 
  
def get_conversation_chain(vactorstore):
    #llm = ChatOpenAI()
    llm = huggingface_hub(repo_id='google/flan-t5-xxl', model_kwargs={'temprature':0.5, "max_length":512})
    memory = ConversationBufferMemory(memory_key='chat_hestory', return_message=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vactorstore.as_retriver,
        memory=memory
    )
    return conversation_chain


def handle_userinput(user_question):
    response = st.session_state.conversation({'question': user_question})
    st.session_state.chat_history = response['chat_history']

    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)
            
            
def main():
    load_dotenv()
    st.set_page_config(page_title='Chat with your Insurance Document', page_icon=':books:')
    st.write(css, unsafe_allow_html=True)

    if 'conversation' not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    st.header('Chat with your Insurance Document :books:')
    user_questions = st.text_input('Write your question here: ')

    if user_questions:
        handle_userinput(user_questions)

    with st.sidebar:
        st.subheader('Your documents')
        pdf_docs = st.file_uploader(
            'Upload your pdf here and click on "process" ', accept_multiple_files=True)
        
        if st.button('process'):
            with st.spinner('processing'):
                #get the text
                row_text = get_pdf_text(pdf_docs)
                if row_text is not None:
                    # get the text chunks
                    text_chunks = get_text_chunks(row_text)
                    st.write(text_chunks)

                    # create vactore store
                    vactorstore = get_vector_store(text_chunks)

                    # create conversation chain
                    st.session_state.conversation = get_conversation_chain(vactorstore)
                else:
                    st.error("Failed to read the PDF. Please upload a different file.")




if __name__ == ('__main__'):
    main()
