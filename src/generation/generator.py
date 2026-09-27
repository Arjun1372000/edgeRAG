from pathlib import Path
import yaml

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama


ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT_DIR / "config" / "config.yaml"


SYSTEM_PROMPT = """
You are the maintenance intelligence component of an
edge-deployed predictive maintenance system.

Your job is to produce a concise, technically grounded
maintenance report from:

1. A machine-condition prediction.
2. Retrieved maintenance evidence.

IMPORTANT RULES:

- Use ONLY the supplied machine condition and retrieved evidence.
- Do not invent procedures, thresholds, causes, or safety instructions.
- Do not override or contradict the retrieved documentation.
- When the evidence does not establish something, explicitly say
  that it is not established by the available evidence.
- Treat model predictions as predictions, not absolute facts.
- Distinguish observed sensor values from inferred/diagnostic conclusions.
- Preserve safety restrictions stated in the retrieved documentation.
- Do not claim that a failure has been physically confirmed unless
  the evidence explicitly supports that claim.

Produce the report using exactly these sections:

# Maintenance Incident Report

## 1. Incident Summary
State the predicted condition, failure probability, and severity/status.

## 2. Observed Machine State
List the relevant sensor values supplied by the machine-condition object.

## 3. Diagnostic Assessment
Explain what the model predicted and what retrieved evidence supports
or does not support that diagnosis.

## 4. Immediate Actions
List only actions explicitly supported by the retrieved evidence.

## 5. Diagnostic Checks
List relevant checks supported by the retrieved evidence.

## 6. Escalation
State the documented escalation conditions.

## 7. Restart / Return to Service
State the documented restart requirements.

## 8. Evidence Sources
Reference the supplied source identifiers such as [S1], [S2], etc.
Do not invent source identifiers.
"""


def load_config():
    with open(
        CONFIG_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        return yaml.safe_load(file)


class EdgeRAGGenerator:

    def __init__(self):
        self.config = load_config()

        llm_config = self.config["llm"]

        if llm_config["provider"].lower() != "ollama":
            raise ValueError(
                f"Unsupported LLM provider: "
                f"{llm_config['provider']}"
            )

        self.llm = ChatOllama(
            model=llm_config["model"],
            temperature=llm_config["temperature"],
            num_predict=llm_config["num_predict"],
            validate_model_on_init=True,
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    SYSTEM_PROMPT,
                ),
                (
                    "human",
                    """
MACHINE CONDITION
-----------------
{machine_condition}


RETRIEVED EVIDENCE
------------------
{context}


Generate the maintenance incident report.
""",
                ),
            ]
        )

    @staticmethod
    def _format_machine_condition(
        machine_condition,
    ) -> str:

        condition = (
            machine_condition.to_dict()
            if hasattr(
                machine_condition,
                "to_dict",
            )
            else machine_condition
        )

        return (
            f"Status: {condition['status']}\n"
            f"Failure probability: "
            f"{condition['failure_probability']}\n"
            f"Predicted failure: "
            f"{condition['predicted_failure']}\n"
            f"Diagnosis: "
            f"{condition['diagnosis']}\n"
            f"Sensor state: "
            f"{condition['sensor_state']}\n"
        )

    @staticmethod
    def _format_context(
        retrieved_documents,
    ) -> str:

        sections = []

        for index, (document, score) in enumerate(
            retrieved_documents,
            start=1,
        ):

            source_id = f"S{index}"

            filename = document.metadata.get(
                "filename",
                "unknown",
            )

            document_type = document.metadata.get(
                "document_type",
                "unknown",
            )

            failure_code = document.metadata.get(
                "failure_code",
                document.metadata.get(
                    "related_failure_codes",
                    "",
                ),
            )

            sections.append(
                f"[{source_id}]\n"
                f"Source: {filename}\n"
                f"Document type: {document_type}\n"
                f"Failure relevance: {failure_code}\n"
                f"Retrieval score: {score:.4f}\n"
                f"Content:\n"
                f"{document.page_content}"
            )

        return "\n\n".join(sections)

    def generate(
        self,
        machine_condition,
        retrieved_documents,
    ) -> str:

        machine_context = (
            self._format_machine_condition(
                machine_condition
            )
        )

        evidence_context = (
            self._format_context(
                retrieved_documents
            )
        )

        chain = (
            self.prompt
            | self.llm
        )

        response = chain.invoke(
            {
                "machine_condition": machine_context,
                "context": evidence_context,
            }
        )

        return response.content