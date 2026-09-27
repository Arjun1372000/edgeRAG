import pandas as pd

from src.models.predictor import PredictiveMaintenanceModel


DATA_PATH = "data/ai4i2020.csv"


FEATURE_COLUMNS = [
    "Type",
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
]

FAULT_COLUMNS = [
    "TWF",
    "HDF",
    "PWF",
    "OSF",
    "RNF",
]


def get_example_row(df, fault=None):

    if fault is not None:

        # Prefer an example where this is the
        # only recorded failure mode.
        isolated = df[
            (df[fault] == 1)
            &
            (df[FAULT_COLUMNS].sum(axis=1) == 1)
        ]

        if not isolated.empty:
            return isolated.iloc[0]

        positives = df[df[fault] == 1]

        if not positives.empty:
            return positives.iloc[0]

    # Normal machine
    normal = df[
        df["Machine failure"] == 0
    ]

    return normal.iloc[0]


def main():

    df = pd.read_csv(DATA_PATH)

    model = PredictiveMaintenanceModel()

    test_cases = [
        ("NORMAL", get_example_row(df)),
    ]

    for fault in FAULT_COLUMNS:
        row = get_example_row(
            df,
            fault,
        )

        test_cases.append(
            (fault, row)
        )

    for expected, row in test_cases:

        sensor_data = {
            column: row[column]
            for column in FEATURE_COLUMNS
        }

        result = model.predict(
            sensor_data
        )

        actual_faults = [
            fault
            for fault in FAULT_COLUMNS
            if row[fault] == 1
        ]

        print("\n" + "=" * 70)

        print(
            f"Expected scenario: {expected}"
        )

        print(
            f"Actual dataset faults: "
            f"{actual_faults}"
        )

        print(
            f"Actual machine failure: "
            f"{row['Machine failure']}"
        )

        print("\nSensor state:")

        for key, value in sensor_data.items():
            print(
                f"  {key}: {value}"
            )

        print("\nModel output:")

        print(
            f"  Failure probability: "
            f"{result['failure_probability']}"
        )

        print(
            f"  Predicted failure: "
            f"{result['predicted_failure']}"
        )

        print(
            f"  Criticality: "
            f"{result['criticality']}"
        )

        print(
            f"  Primary fault: "
            f"{result['primary_fault']}"
        )

        print("\nFault candidates:")

        for candidate in result[
            "fault_candidates"
        ]:
            print(
                f"  {candidate['fault']}: "
                f"{candidate['probability']:.4f} "
                f"(threshold "
                f"{candidate['threshold']:.3f})"
            )


if __name__ == "__main__":
    main()