from dataclasses import dataclass, asdict

from src.models.predictor import PredictiveMaintenanceModel


@dataclass
class MachineCondition:
    status: str
    failure_probability: float
    predicted_failure: bool
    diagnosis: str
    fault_candidates: list
    sensor_state: dict
    retrieval_query: str

    def to_dict(self):
        return asdict(self)


class MachineConditionBuilder:

    def __init__(self):
        self.model = PredictiveMaintenanceModel()

    def analyze(
        self,
        sensor_data: dict,
    ) -> MachineCondition:

        prediction = self.model.predict(sensor_data)

        diagnosis = prediction["diagnosis"]

        retrieval_query = self._build_retrieval_query(
            prediction=prediction,
            sensor_data=sensor_data,
        )

        return MachineCondition(
            status=prediction["criticality"],
            failure_probability=prediction[
                "failure_probability"
            ],
            predicted_failure=prediction[
                "predicted_failure"
            ],
            diagnosis=diagnosis,
            fault_candidates=prediction[
                "fault_candidates"
            ],
            sensor_state=sensor_data,
            retrieval_query=retrieval_query,
        )

    @staticmethod
    def _build_retrieval_query(
        prediction: dict,
        sensor_data: dict,
    ) -> str:

        diagnosis = prediction["diagnosis"]

        failure_probability = (
            prediction["failure_probability"]
        )

        query = (
            "Industrial machine maintenance event. "
            f"Machine failure probability is "
            f"{failure_probability:.2f}. "
        )

        if diagnosis != "NORMAL":
            query += (
                f"Detected condition: {diagnosis}. "
            )

        query += (
            "Retrieve relevant maintenance procedures, "
            "diagnostic checks, mitigation actions, "
            "safety requirements, escalation conditions, "
            "and restart requirements. "
        )

        query += (
            "Observed machine parameters: "
            f"air temperature "
            f"{sensor_data['Air temperature [K]']} K, "
            f"process temperature "
            f"{sensor_data['Process temperature [K]']} K, "
            f"rotational speed "
            f"{sensor_data['Rotational speed [rpm]']} RPM, "
            f"torque "
            f"{sensor_data['Torque [Nm]']} Nm, "
            f"tool wear "
            f"{sensor_data['Tool wear [min]']} minutes."
        )

        return query