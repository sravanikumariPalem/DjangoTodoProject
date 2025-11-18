# tasks/rag_utils.py
import os
import csv

from pypdf import PdfReader
from docx import Document as DocxDocument  # rename to avoid clash

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama

# Depending on your langchain version, use ONE of these:
try:
    from langchain_core.documents import Document  # new style
except ImportError:
    from langchain.schema import Document          # fallback for older versions


# ---------------- FILE EXTRACTORS ---------------- #

def extract_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += (page.extract_text() or "") + "\n"
    return text


def extract_docx(file_path: str) -> str:
    doc = DocxDocument(file_path)
    return "\n".join(p.text for p in doc.paragraphs)


def extract_csv(file_path: str) -> str:
    text = ""
    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            text += " | ".join(row) + "\n"
    return text


def extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        return extract_docx(file_path)
    elif ext == ".csv":
        return extract_csv(file_path)
    else:
        return ""  # unsupported file


# ---------------- INDEX DOCUMENTS (MULTI-DOC) ---------------- #

def index_documents(text: str, persist_directory: str = "chroma_db"):
    """
    Chunk text, create embeddings, and store in (or append to) a Chroma DB.

    - If the DB folder exists and is non-empty, we *append* new chunks.
    - Otherwise, we create a fresh Chroma DB.
    """
    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(text)

    docs = [Document(page_content=chunk) for chunk in chunks]

    # Embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # If DB exists, load and append; otherwise create
    if os.path.exists(persist_directory) and os.listdir(persist_directory):
        vectordb = Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings,
        )
        vectordb.add_documents(docs)
    else:
        vectordb = Chroma.from_documents(
            docs,
            embeddings,
            persist_directory=persist_directory,
        )

    vectordb.persist()
    return vectordb


# ---------------- CREATE RAG CHAIN ---------------- #

def get_qa_chain(persist_directory: str = "chroma_db"):
    """
    Returns a callable `rag_answer(question: str) -> str` using
    Chroma + local Ollama.
    """
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vectordb = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
    )
    retriever = vectordb.as_retriever(search_kwargs={"k": 4})

    llm = Ollama(model="llama3", temperature=0)

    def rag_answer(question: str) -> str:
        docs = retriever.get_relevant_documents(question)
        context = "\n\n".join(d.page_content for d in docs)

        prompt = f"""
You are a helpful assistant. Use ONLY the following context to answer the question.
If the context is not relevant, say you don't know.

Context:
{context}

Question:
{question}

Answer:
""".strip()

        return llm(prompt)

    return rag_answer
