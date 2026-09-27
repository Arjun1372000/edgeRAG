import pandas as pd

from src.pipeline.machine_condition import (
    MachineConditionBuilder,
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

    failure_rows = df[
        df["Machine failure"] == 1
    ]

    row = failure_rows.iloc[0]

    sensor_data = {
        column: row[column]
        for column in FEATURE_COLUMNS
    }

    builder = MachineConditionBuilder()

    condition = builder.analyze(
        sensor_data=sensor_data,
    )

    print("=" * 70)
    print("EdgeRAG Machine Condition Test")
    print("=" * 70)

    print("\nMachine Condition:")

    result = condition.to_dict()

    for key, value in result.items():

        if key == "retrieval_query":
            continue

        print(f"\n{key}:")

        if isinstance(value, dict):
            for item_key, item_value in value.items():
                print(
                    f"  {item_key}: {item_value}"
                )

        elif isinstance(value, list):
            for item in value:
                print(
                    f"  {item}"
                )

        else:
            print(
                f"  {value}"
            )

    print("\nRetrieval Query:")
    print(condition.retrieval_query)


if __name__ == "__main__":
    main()