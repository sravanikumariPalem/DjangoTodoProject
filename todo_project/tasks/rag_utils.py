# tasks/rag_utils.py
import os
import csv
from pypdf import PdfReader
from docx import Document

# LangChain Community (new API)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
# ---------------- FILE EXTRACTORS ---------------- #

def extract_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += (page.extract_text() or "") + "\n"
    return text

def extract_docx(file_path):
    doc = Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs])

def extract_csv(file_path):
    text = ""
    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            text += " | ".join(row) + "\n"
    return text

def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        return extract_docx(file_path)
    elif ext == ".csv":
        return extract_csv(file_path)
    else:
        return ""  # unsupported file

# ---------------- INDEX DOCUMENTS ---------------- #

def index_documents(text, persist_directory="chroma_db"):
    """
    Chunk text, create embeddings using HuggingFace locally, and store in Chroma vector DB.
    """
    # Split text into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(text)

    # Wrap chunks as LangChain Documents
    docs = [Document(page_content=chunk) for chunk in chunks]

    # Embeddings (HuggingFace local model)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Chroma vector store
    vectordb = Chroma.from_documents(docs, embeddings, persist_directory=persist_directory)
    vectordb.persist()
    return vectordb

# ---------------- CREATE RAG CHAIN ---------------- #

def get_qa_chain(persist_directory="chroma_db"):
    """
    Returns a callable function that takes a question and answers using local Ollama + Chroma.
    """
    # Load Chroma vector store
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectordb = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
    retriever = vectordb.as_retriever(search_kwargs={"k": 4})

    # Local LLM (Ollama)
    llm = Ollama(model="llama3", temperature=0)

    def rag_answer(question: str) -> str:
        # Retrieve relevant documents
        docs = retriever.get_relevant_documents(question)
        context = "\n\n".join([d.page_content for d in docs])

        # Prepare prompt
        prompt = f"""
You are a helpful assistant. Use the following context to answer the question.

Context:
{context}

Question:
{question}

Answer:
"""

        # Generate answer from Ollama
        return llm(prompt)

    return rag_answer
