from src.models.predictor import PredictiveMaintenanceModel


def main():

    model = PredictiveMaintenanceModel()

    sample = {
        "Type": "M",
        "Air temperature [K]": 301.2,
        "Process temperature [K]": 312.4,
        "Rotational speed [rpm]": 1290,
        "Torque [Nm]": 43.2,
        "Tool wear [min]": 178,
    }

    result = model.predict(sample)

    print("=" * 60)
    print("EdgeRAG Predictive Maintenance Test")
    print("=" * 60)

    print("\nFailure Probability:")
    print(result["failure_probability"])

    print("\nPredicted Failure:")
    print(result["predicted_failure"])

    print("\nCriticality:")
    print(result["criticality"])

    print("\nPrimary Fault:")
    print(result["primary_fault"])

    print("\nFault Probabilities:")

    for fault, probability in result[
        "fault_probabilities"
    ].items():
        print(
            f"  {fault}: {probability}"
        )


if __name__ == "__main__":
    main()