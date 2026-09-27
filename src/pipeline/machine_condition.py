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
        failure_probability = prediction[
            "failure_probability"
        ]

        query_parts = [
            "Industrial machine maintenance event.",
            (
                f"Machine failure probability is "
                f"{failure_probability:.2f}."
            ),
        ]

        if diagnosis not in {
            "NORMAL",
            "UNKNOWN",
            "UNCLASSIFIED_FAILURE",
        }:
            query_parts.append(
                f"Detected condition: {diagnosis}."
            )
        else:
            query_parts.append(
                f"Detected condition: {diagnosis}."
            )

        if diagnosis == "PWF":

            power_proxy = (
                sensor_data["Rotational speed [rpm]"]
                * sensor_data["Torque [Nm]"]
            )

            query_parts.append(
                "Inferred power proxy from "
                "Torque × Rotational Speed is "
                f"{power_proxy:.1f}."
            )

            query_parts.append(
                "Prioritize evidence related to "
                "power delivery, electrical diagnostics, "
                "electrical isolation, inverter faults, "
                "mitigation, escalation, and controlled restart."
            )

        elif diagnosis == "HDF":

            temperature_delta = (
                sensor_data["Process temperature [K]"]
                - sensor_data["Air temperature [K]"]
            )

            query_parts.append(
                f"Process-to-air temperature difference "
                f"is {temperature_delta:.1f} K."
            )

            query_parts.append(
                "Prioritize evidence related to "
                "cooling, thermal diagnostics, ventilation, "
                "mitigation, escalation, and restart."
            )

        elif diagnosis == "TWF":

            query_parts.append(
                "Prioritize evidence related to "
                "tool wear, tool inspection, tool replacement, "
                "torque trends, spindle safety, and restart."
            )

        elif diagnosis == "OSF":

            query_parts.append(
                "Prioritize evidence related to "
                "mechanical overstrain, torque spikes, "
                "binding, workpiece inspection, safety, "
                "and controlled restart."
            )

        else:

            query_parts.append(
                "Retrieve general failure investigation, "
                "diagnostic, safety, mitigation, escalation, "
                "and restart evidence."
            )

        query_parts.append(
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

        return " ".join(query_parts)