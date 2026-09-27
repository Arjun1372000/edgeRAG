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

        embedding_config = self.config[
            "embedding"
        ]

        if (
            embedding_config["provider"].lower()
            != "ollama"
        ):
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

        retrieval_config = self.config[
            "retrieval"
        ]

        self.top_k = retrieval_config[
            "top_k"
        ]

        self.semantic_k = retrieval_config[
            "semantic_k"
        ]

        self.fault_k = retrieval_config[
            "fault_k"
        ]

        self.max_chunks_per_source = (
            retrieval_config[
                "max_chunks_per_source"
            ]
        )

        self.reranking_config = (
            retrieval_config[
                "reranking"
            ]
        )

    def _fault_matches(
        self,
        document,
        failure_code: str,
    ) -> bool:

        if not failure_code:
            return False

        failure_code = (
            failure_code.upper()
        )

        metadata = document.metadata

        primary = metadata.get(
            "failure_code",
            "",
        ).upper()

        related = metadata.get(
            "related_failure_codes",
            "",
        ).upper()

        if primary == failure_code:
            return True

        related_codes = {
            code.strip()
            for code in related.split(",")
            if code.strip()
        }

        return failure_code in related_codes

    def _calculate_rerank_score(
        self,
        document,
        semantic_score: float,
        failure_code: str | None,
    ) -> float:

        score = semantic_score

        # -----------------------------------------------------
        # Fault relevance
        # -----------------------------------------------------

        if self._fault_matches(
            document,
            failure_code,
        ):
            score += self.reranking_config[
                "fault_bonus"
            ]

        # -----------------------------------------------------
        # Document-type bonus
        #
        # Small bonus only. Semantic similarity remains
        # the dominant signal.
        # -----------------------------------------------------

        document_type = document.metadata.get(
            "document_type",
            "general",
        )

        if document_type in {
            "sop",
            "diagnostics",
            "safety",
            "maintenance",
            "restart",
        }:
            score += self.reranking_config[
                "document_type_bonus"
            ]

        # -----------------------------------------------------
        # Severity bonus
        # -----------------------------------------------------

        severity = document.metadata.get(
            "severity",
            "",
        ).lower()

        if severity in {
            "critical",
            "high",
        }:
            score += self.reranking_config[
                "severity_bonus"
            ]

        return score

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

        final_k = top_k or self.top_k

        # -----------------------------------------------------
        # 1. Global semantic retrieval
        # -----------------------------------------------------

        semantic_results = (
            self.vectorstore
            .similarity_search_with_relevance_scores(
                query,
                k=self.semantic_k,
            )
        )

        # -----------------------------------------------------
        # 2. Fault-focused semantic retrieval
        # -----------------------------------------------------

        fault_results = []

        if failure_code:
            fault_results = (
                self.vectorstore
                .similarity_search_with_relevance_scores(
                    query,
                    k=self.fault_k,
                    filter={
                        "$or": [
                            {
                                "failure_code":
                                failure_code
                            },
                            {
                                "related_failure_codes":
                                failure_code
                            },
                        ]
                    },
                )
            )

        # -----------------------------------------------------
        # 3. Merge candidates
        # -----------------------------------------------------

        candidates = {}

        for document, semantic_score in (
            semantic_results
            + fault_results
        ):

            source = document.metadata.get(
                "source",
                document.metadata.get(
                    "filename",
                    "unknown",
                ),
            )

            content = document.page_content

            key = (
                source,
                content,
            )

            rerank_score = (
                self._calculate_rerank_score(
                    document=document,
                    semantic_score=semantic_score,
                    failure_code=failure_code,
                )
            )

            if key not in candidates:

                candidates[key] = {
                    "document": document,
                    "semantic_score": semantic_score,
                    "rerank_score": rerank_score,
                }

            else:

                candidates[key][
                    "semantic_score"
                ] = max(
                    candidates[key][
                        "semantic_score"
                    ],
                    semantic_score,
                )

                candidates[key][
                    "rerank_score"
                ] = max(
                    candidates[key][
                        "rerank_score"
                    ],
                    rerank_score,
                )

        # -----------------------------------------------------
        # 4. Rank by reranked score
        # -----------------------------------------------------

        ranked = sorted(
            candidates.values(),
            key=lambda item: item[
                "rerank_score"
            ],
            reverse=True,
        )

        # -----------------------------------------------------
        # 5. Diversify by source
        # -----------------------------------------------------

        selected = []
        source_counts = {}

        # First pass: one chunk per source
        for item in ranked:

            document = item["document"]

            source = document.metadata.get(
                "filename",
                "unknown",
            )

            count = source_counts.get(
                source,
                0,
            )

            if count > 0:
                continue

            selected.append(
                (
                    document,
                    item["rerank_score"],
                )
            )

            source_counts[source] = 1

            if len(selected) >= final_k:
                return selected

        # Second pass: permit a second chunk
        # from high-value sources.
        for item in ranked:

            document = item["document"]

            source = document.metadata.get(
                "filename",
                "unknown",
            )

            count = source_counts.get(
                source,
                0,
            )

            if count >= self.max_chunks_per_source:
                continue

            already_selected = any(
                selected_document.page_content
                == document.page_content
                for selected_document, _ in selected
            )

            if already_selected:
                continue

            selected.append(
                (
                    document,
                    item["rerank_score"],
                )
            )

            source_counts[source] = count + 1

            if len(selected) >= final_k:
                break

        return selected