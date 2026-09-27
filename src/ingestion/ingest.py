from pathlib import Path
import sys
import yaml

from src.ingestion.loader import load_documents
from src.ingestion.indexer import (
    create_embeddings,
    split_documents,
    create_vectorstore,
)


ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT_DIR / "config" / "config.yaml"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def main():
    config = load_config()

    documents_path = (
        ROOT_DIR / config["documents"]["path"]
    )

    extensions = [
        extension.lower()
        for extension in config["documents"]["extensions"]
    ]

    chunking_config = config["chunking"]
    embedding_config = config["embedding"]
    vectorstore_config = config["vectorstore"]

    print("=" * 60)
    print("EdgeRAG Document Ingestion")
    print("=" * 60)

    print(f"\nDocuments: {documents_path}")

    print("\n[1/4] Loading documents...")
    documents = load_documents(
        documents_path=str(documents_path),
        extensions=extensions,
    )
    print(f"Loaded {len(documents)} document(s)")

    print("\n[2/4] Splitting documents...")

    chunks = split_documents(
        documents=documents,
        chunk_size=chunking_config["chunk_size"],
        chunk_overlap=chunking_config["chunk_overlap"],
    )

    print(f"Created {len(chunks)} chunks")

    print("\n[3/4] Loading embedding model...")

    print(
        f"Provider: {embedding_config['provider']}"
    )
    print(
        f"Model: {embedding_config['model']}"
    )

    if embedding_config["provider"].lower() != "ollama":
        raise ValueError(
            f"Unsupported embedding provider: "
            f"{embedding_config['provider']}"
        )

    embeddings = create_embeddings(
        embedding_config["model"]
    )

    # Small sanity check before embedding the corpus
    test_vector = embeddings.embed_query(
        "machine failure maintenance"
    )

    print(
        f"Embedding dimension: {len(test_vector)}"
    )

    print("\n[4/4] Creating Chroma vector store...")

    vectorstore_path = (
        ROOT_DIR / vectorstore_config["path"]
    )

    create_vectorstore(
        documents=chunks,
        embeddings=embeddings,
        persist_directory=str(vectorstore_path),
        collection_name=vectorstore_config[
            "collection_name"
        ],
    )

    print(
        f"\nStored {len(chunks)} vectors in Chroma"
    )

    print(
        f"Location: {vectorstore_path}"
    )

    print("\nIngestion completed successfully.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nERROR: {exc}")
        sys.exit(1)