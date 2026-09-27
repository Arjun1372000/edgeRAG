import pandas as pd

from src.data.validation import validate_dataset


DATA_PATH = "data/ai4i2020.csv"


def main():

    df = pd.read_csv(DATA_PATH)

    clean_df, report = validate_dataset(
        df,
        exclude_inconsistent_labels=True,
    )

    print("=" * 70)
    print("EdgeRAG Dataset Validation")
    print("=" * 70)

    print(
        f"\nRaw rows: "
        f"{report['rows_total']}"
    )

    print(
        f"Clean rows: "
        f"{report['rows_used_for_training']}"
    )

    print(
        f"Excluded rows: "
        f"{report['rows_excluded_from_training']}"
    )

    print(
        f"\nDuplicate rows: "
        f"{report['duplicate_rows']}"
    )

    print(
        f"Invalid Type rows: "
        f"{report['invalid_type_rows']}"
    )

    print(
        f"Invalid numeric rows: "
        f"{report['invalid_numeric_rows']}"
    )

    print(
        f"Invalid binary-label rows: "
        f"{report['invalid_binary_label_rows']}"
    )

    print(
        f"Label inconsistencies: "
        f"{report['label_inconsistency_rows']}"
    )

    print("\nFailure counts:")

    for fault, count in report[
        "fault_counts"
    ].items():
        print(
            f"  {fault}: {count}"
        )

    if report[
        "label_inconsistency_examples"
    ]:

        print("\nInconsistency examples:")

        for example in report[
            "label_inconsistency_examples"
        ]:
            print(
                f"  Row {example['index']}: "
                f"machine_failure="
                f"{example['machine_failure']}, "
                f"faults="
                f"{example['faults']}"
            )

    print("\nValidation completed.")


if __name__ == "__main__":
    main()