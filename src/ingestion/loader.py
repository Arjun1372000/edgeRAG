from pathlib import Path
import re

from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document


def extract_metadata(
    file_path: Path,
    document: Document,
) -> dict:
    metadata = {
        "source": str(file_path),
        "filename": file_path.name,
    }

    text = document.page_content

    patterns = {
        "document_id": r"DOCUMENT ID:\s*(.+)",
        "title": r"TITLE:\s*(.+)",
        "failure_code": r"FAILURE CODE:\s*(.+)",
        "applies_to": r"APPLIES TO:\s*(.+)",
        "severity": r"SEVERITY:\s*(.+)",
    }

    for key, pattern in patterns.items():
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            metadata[key] = match.group(1).strip()

    metadata["document_type"] = (
        "SOP"
        if file_path.name.upper().startswith("SOP-")
        else "GENERAL"
    )

    return metadata


def load_documents(
    documents_path: str,
    extensions: list[str],
) -> list[Document]:
    path = Path(documents_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Documents directory does not exist: {path}"
        )

    documents = []

    for file_path in sorted(path.rglob("*")):
        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in extensions:
            continue

        if file_path.suffix.lower() != ".txt":
            raise NotImplementedError(
                f"Loader for {file_path.suffix} "
                f"is not implemented yet."
            )

        loaded_documents = TextLoader(
            str(file_path),
            encoding="utf-8",
        ).load()

        for document in loaded_documents:
            document.metadata.update(
                extract_metadata(
                    file_path,
                    document,
                )
            )

        documents.extend(loaded_documents)

    if not documents:
        raise ValueError(
            f"No supported documents found in {path}"
        )

    return documents