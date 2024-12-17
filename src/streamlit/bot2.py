import streamlit as st
import os
import pandas as pd
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from sentence_transformers import SentenceTransformer
import faiss
from transformers import AutoTokenizer
from vllm import LLM, SamplingParams
from pathlib import Path
import requests

api_url = "http://localhost:8000/v1/chat/completions"

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

# model_name = "ai-sage/GigaChat-20B-A3B-instruct"
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# llm = LLM(model=model_name, trust_remote_code=True, tensor_parallel_size=2, max_model_len=20000)
# sampling_params = SamplingParams(temperature=0.3, max_tokens=500)

############################################################################################################################################################

system_message = prompt_content

def answer_question_vllm(input_text):
    retrieved_docs = retriever.get_relevant_documents(input_text, k=10)
    context = "\n\n".join([doc.page_content for doc in retrieved_docs])

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"Контекст: {context}\n\nВопрос: {input_text}"}
    ]

    payload = {
        "model": "ai-sage/GigaChat-20B-A3B-instruct",
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 1000
    }

    response = requests.post(api_url, json=payload)

    if response.status_code == 200:
        generated_text = response.json()["choices"][0]["message"]["content"]
        return generated_text
    else:
        st.error(f"Ошибка API: {response.status_code} - {response.text}")
        return "Произошла ошибка при генерации ответа."

############################################################################################################################################################

st.title("Chat-BOT (vLLM)")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Введите ваш запрос о доме:"):

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    response = answer_question_vllm(prompt)
    st.session_state.messages.append({"role": "assistant", "content": response})

    with st.chat_message("assistant"):
        st.markdown(response)
