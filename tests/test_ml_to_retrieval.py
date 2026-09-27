import pandas as pd

from src.pipeline.machine_condition import (
    MachineConditionBuilder,
)
from src.retrieval.retriever import (
    EdgeRAGRetriever,
)


DATA_PATH = "data/ai4i2020.csv"

FEATURE_COLUMNS = [
    "Type",
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
]


def main():

    df = pd.read_csv(DATA_PATH)

    # Use a known machine-failure example.
    row = df[
        df["Machine failure"] == 1
    ].iloc[0]

    sensor_data = {
        column: row[column]
        for column in FEATURE_COLUMNS
    }

    condition_builder = MachineConditionBuilder()

    condition = condition_builder.analyze(
        sensor_data
    )

    retriever = EdgeRAGRetriever()

    failure_code = (
        condition.diagnosis
        if condition.diagnosis
        not in {
            "UNKNOWN",
            "UNCLASSIFIED_FAILURE",
            "NORMAL",
        }
        else None
    )

    results = retriever.retrieve(
        condition.retrieval_query,
        failure_code=failure_code,
    )

    print("=" * 70)
    print("EdgeRAG: ML → Retrieval Test")
    print("=" * 70)

    print("\nMachine Condition:")
    print(
        f"Status: {condition.status}"
    )
    print(
        f"Failure probability: "
        f"{condition.failure_probability}"
    )
    print(
        f"Diagnosis: {condition.diagnosis}"
    )

    print("\nGenerated Retrieval Query:")
    print(condition.retrieval_query)

    print("\nRetrieved Documents:")

    for rank, (document, score) in enumerate(
        results,
        start=1,
    ):
        print("\n" + "-" * 70)
        print(f"Rank: {rank}")
        print(f"Score: {score:.4f}")
        print(
            "Source: "
            f"{document.metadata.get('filename', 'unknown')}"
        )
        print(
            "Preview: "
            f"{document.page_content[:250]}..."
        )


if __name__ == "__main__":
    main()