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
        "related_failure_codes": r"RELATED FAILURE CODES:\s*(.+)",
    }

    for key, pattern in patterns.items():
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            value = match.group(1).strip()

            if key == "related_failure_codes":
                codes = [
                    code.strip().upper()
                    for code in value.split(",")
                    if code.strip()
                ]

                metadata[key] = ",".join(codes)
            else:
                metadata[key] = value

    # ---------------------------------------------------------
    # Document type from directory structure
    # ---------------------------------------------------------

    parent_folder = file_path.parent.name.lower()

    document_type_map = {
        "sops": "sop",
        "diagnostics": "diagnostics",
        "safety": "safety",
        "maintenance": "maintenance",
        "restart": "restart",
    }

    metadata["document_type"] = (
        document_type_map.get(
            parent_folder,
            "general",
        )
    )

    # ---------------------------------------------------------
    # Normalize failure-code metadata
    # ---------------------------------------------------------

    if "failure_code" in metadata:
        metadata["failure_code"] = (
            metadata["failure_code"]
            .strip()
            .upper()
        )

        metadata["related_failure_codes"] = (
            metadata["failure_code"]
        )

    elif "related_failure_codes" not in metadata:
        metadata["related_failure_codes"] = ""

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

        documents.extend(
            loaded_documents
        )

    if not documents:
        raise ValueError(
            f"No supported documents found in {path}"
        )

    return documents