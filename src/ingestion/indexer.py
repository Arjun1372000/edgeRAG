from pathlib import Path

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


def create_embeddings(model_name: str):
    return OllamaEmbeddings(
        model=model_name,
    )


def split_documents(
    documents,
    chunk_size: int,
    chunk_overlap: int,
):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            "",
        ],
    )

    return splitter.split_documents(documents)


def create_vectorstore(
    documents,
    embeddings,
    persist_directory: str,
    collection_name: str,
):
    Path(persist_directory).mkdir(
        parents=True,
        exist_ok=True,
    )

    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_directory,
    )

    vectorstore.reset_collection()

    vectorstore.add_documents(
        documents=documents,
    )

    return vectorstore