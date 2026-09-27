from pathlib import Path
import yaml

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings


ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT_DIR / "config" / "config.yaml"


def load_config():
    with open(
        CONFIG_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        return yaml.safe_load(file)


class EdgeRAGRetriever:

    def __init__(self):
        self.config = load_config()

        embedding_config = self.config["embedding"]

        if embedding_config["provider"].lower() != "ollama":
            raise ValueError(
                f"Unsupported embedding provider: "
                f"{embedding_config['provider']}"
            )

        embeddings = OllamaEmbeddings(
            model=embedding_config["model"]
        )

        vectorstore_config = self.config[
            "vectorstore"
        ]

        persist_directory = (
            ROOT_DIR
            / vectorstore_config["path"]
        )

        self.vectorstore = Chroma(
            collection_name=vectorstore_config[
                "collection_name"
            ],
            embedding_function=embeddings,
            persist_directory=str(
                persist_directory
            ),
        )

        self.top_k = self.config[
            "retrieval"
        ]["top_k"]

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        failure_code: str | None = None,
    ):
        if not query.strip():
            raise ValueError(
                "Retrieval query cannot be empty."
            )

        if top_k is None:
            top_k = self.top_k

        metadata_filter = None

        if failure_code:
            metadata_filter = {
                "failure_code": failure_code
            }

        return (
            self.vectorstore
            .similarity_search_with_relevance_scores(
                query,
                k=top_k,
                filter=metadata_filter,
            )
        )