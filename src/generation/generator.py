from pathlib import Path
import yaml

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama


ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT_DIR / "config" / "config.yaml"


SYSTEM_PROMPT = """
You are the maintenance-report generator for a fully local
predictive-maintenance system.

You receive:

1. A MachineCondition object produced by a predictive model.
2. Retrieved maintenance documents.

Your job is to produce a factual maintenance report grounded ONLY
in those inputs.

STRICT RULES:

1. Do not invent facts, causes, actions, thresholds, or procedures.

2. Do not recalculate sensor-derived values.
   When the MachineCondition provides a derived value or diagnosis,
   repeat it exactly.

3. Treat the MachineCondition as the source of truth for:
   - failure probability
   - status
   - diagnosis
   - sensor readings
   - derived diagnostic values

4. Treat retrieved documents as the source of truth for:
   - symptoms
   - root causes
   - mitigation actions
   - diagnostic checks
   - escalation conditions
   - restart requirements
   - safety requirements

5. Every recommended action must be supported by at least one
   retrieved source.

6. Do not say that information is unavailable if it is explicitly
   present in one of the supplied sources.

7. Do not infer that a sensor value is abnormal unless the supplied
   evidence establishes the relevant threshold or condition.

8. Do not describe the machine as physically confirmed to have failed.
   The predictive model produces a prediction, not physical confirmation.

9. Do not introduce information from general knowledge.

10. When sources disagree or evidence is insufficient, explicitly state
    that the evidence is insufficient.

SOURCE CITATION RULE:

Every factual statement derived from retrieved evidence should end
with its source identifier, for example:

The machine should be isolated from the main grid. [S1]

Do not invent source identifiers.

REPORT FORMAT:

# Maintenance Incident Report

## 1. Incident Summary
State the model status, failure probability, and diagnosis.

## 2. Observed Machine State
Report the supplied sensor values and supplied derived values exactly.

## 3. Diagnostic Assessment
Explain the diagnosis using only the MachineCondition and retrieved evidence.

## 4. Immediate Actions
List only explicitly documented mitigation or safety actions.

## 5. Diagnostic Checks
List only explicitly documented checks relevant to this event.

## 6. Escalation
State the documented escalation conditions.

## 7. Restart / Return to Service
State the documented restart conditions.

## 8. Evidence Sources
List the source identifiers and filenames used.
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