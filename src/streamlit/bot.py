import streamlit as st
import os
import pandas as pd
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from sentence_transformers import SentenceTransformer
from langchain_ollama.llms import OllamaLLM
from langchain.schema import HumanMessage, SystemMessage
import faiss
from pathlib import Path

############################################################################################################################################################

prompt_path = Path("data/system_prompt.txt")

with prompt_path.open("r", encoding="utf-8") as file:
    prompt_content = file.read()
    
############################################################################################################################################################

if "messages" not in st.session_state:
    st.session_state.messages = []

file_path = 'data/final_data.csv'
loader = CSVLoader(file_path=file_path)
docs = loader.load_and_split()

############################################################################################################################################################

class SentenceTransformerEmbeddings:
    def __init__(self, model_name="intfloat/multilingual-e5-large-instruct"):
        self.model = SentenceTransformer(model_name)

    def embed_query(self, query):
        return self.model.encode([query], convert_to_tensor=False)[0]

    def embed_documents(self, docs):
        return self.model.encode(docs, convert_to_tensor=False)

embeddings = SentenceTransformerEmbeddings()
embedding_dim = len(embeddings.embed_query(" "))
index = faiss.IndexFlatL2(embedding_dim)
vector_store = FAISS(
    embedding_function=embeddings.embed_query,
    index=index,
    docstore=InMemoryDocstore(),
    index_to_docstore_id={}
)

texts = [doc.page_content for doc in docs]
vector_store.add_texts(texts)

retriever = vector_store.as_retriever()

############################################################################################################################################################

model_name = 'qwen2.5:7b-instruct-q4_0'

model = OllamaLLM(model=model_name,
                  num_ctx=1000,
                  temperature=0.7,
                  top_k=1,
                #   max_tokens=150
                  )

############################################################################################################################################################

system_message = SystemMessage(
    content=prompt_content
)

############################################################################################################################################################

def answer_question(input_text):
    retrieved_docs = retriever.get_relevant_documents(input_text, k=10)
    context = "\n\n".join([doc.page_content for doc in retrieved_docs])

    messages = [
        system_message,
        HumanMessage(content=f"Контекст: {context}\n\nВопрос: {input_text}")
    ]

    response = model.invoke(messages)
    
    if isinstance(response, str):
        return response
    
    return response.get('content', "Не удалось получить ответ.")

############################################################################################################################################################

st.title("Chat-BOT")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Введите ваш запрос о доме:"):
    
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    response = answer_question(prompt)
    st.session_state.messages.append({"role": "assistant", "content": response})

    with st.chat_message("assistant"):
        st.markdown(response)
