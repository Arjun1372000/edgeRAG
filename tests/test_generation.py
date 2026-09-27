import pandas as pd

from src.pipeline.machine_condition import (
    MachineConditionBuilder,
)
from src.retrieval.retriever import (
    EdgeRAGRetriever,
)
from src.generation.generator import (
    EdgeRAGGenerator,
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

    # Start with a known failure case.
    row = df[
        df["Machine failure"] == 1
    ].iloc[0]

    sensor_data = {
        column: row[column]
        for column in FEATURE_COLUMNS
    }

    # ---------------------------------------------------------
    # 1. ML
    # ---------------------------------------------------------

    condition_builder = (
        MachineConditionBuilder()
    )

    condition = condition_builder.analyze(
        sensor_data
    )

    # ---------------------------------------------------------
    # 2. Retrieval
    # ---------------------------------------------------------

    retriever = EdgeRAGRetriever()

    failure_code = (
        condition.diagnosis
        if condition.diagnosis
        not in {
            "NORMAL",
            "UNKNOWN",
            "UNCLASSIFIED_FAILURE",
        }
        else None
    )

    retrieved_documents = (
        retriever.retrieve(
            condition.retrieval_query,
            failure_code=failure_code,
        )
    )

    # ---------------------------------------------------------
    # 3. Generation
    # ---------------------------------------------------------

    generator = EdgeRAGGenerator()

    report = generator.generate(
        machine_condition=condition,
        retrieved_documents=retrieved_documents,
    )

    # ---------------------------------------------------------
    # Output
    # ---------------------------------------------------------

    print("=" * 70)
    print("EdgeRAG End-to-End Generation Test")
    print("=" * 70)

    print("\nMachine Diagnosis:")
    print(
        f"  Status: {condition.status}"
    )
    print(
        f"  Failure probability: "
        f"{condition.failure_probability}"
    )
    print(
        f"  Diagnosis: "
        f"{condition.diagnosis}"
    )

    print("\nRetrieved Evidence:")

    for rank, (document, score) in enumerate(
        retrieved_documents,
        start=1,
    ):
        print(
            f"  [{rank}] "
            f"{document.metadata.get('filename', 'unknown')} "
            f"({score:.4f})"
        )

    print("\n" + "=" * 70)
    print("GENERATED MAINTENANCE REPORT")
    print("=" * 70)
    print()

    print(report)


if __name__ == "__main__":
    main()