from pathlib import Path

import markdown
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.generation.generator import EdgeRAGGenerator
from src.pipeline.machine_condition import MachineConditionBuilder
from src.retrieval.retriever import EdgeRAGRetriever


ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT_DIR / "frontend"
DATA_PATH = ROOT_DIR / "data" / "ai4i2020.csv"


app = FastAPI(
    title="EdgeRAG API",
    description="Local predictive-maintenance RAG service",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


machine_condition_builder = MachineConditionBuilder()
retriever = EdgeRAGRetriever()
generator = EdgeRAGGenerator()


class SensorInput(BaseModel):
    type: str = Field(..., pattern=r"^[LMHlmh]$")
    air_temperature: float = Field(..., ge=0)
    process_temperature: float = Field(..., ge=0)
    rotational_speed: float = Field(..., ge=0)
    torque: float = Field(..., ge=0)
    tool_wear: float = Field(..., ge=0)


def normalize_sensor_input(data: SensorInput) -> dict:
    return {
        "Type": data.type.upper(),
        "Air temperature [K]": data.air_temperature,
        "Process temperature [K]": data.process_temperature,
        "Rotational speed [rpm]": data.rotational_speed,
        "Torque [Nm]": data.torque,
        "Tool wear [min]": data.tool_wear,
    }


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "EdgeRAG",
    }


@app.get("/api/sample")
def sample():
    if not DATA_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="AI4I dataset not found.",
        )

    df = pd.read_csv(DATA_PATH)

    failure_rows = df[
        df["Machine failure"] == 1
    ]

    if failure_rows.empty:
        raise HTTPException(
            status_code=404,
            detail="No failure row found in dataset.",
        )

    row = failure_rows.iloc[0]

    return {
        "type": row["Type"],
        "air_temperature": float(
            row["Air temperature [K]"]
        ),
        "process_temperature": float(
            row["Process temperature [K]"]
        ),
        "rotational_speed": float(
            row["Rotational speed [rpm]"]
        ),
        "torque": float(
            row["Torque [Nm]"]
        ),
        "tool_wear": float(
            row["Tool wear [min]"]
        ),
        "actual_machine_failure": int(
            row["Machine failure"]
        ),
        "actual_faults": [
            fault
            for fault in [
                "TWF",
                "HDF",
                "PWF",
                "OSF",
                "RNF",
            ]
            if int(row[fault]) == 1
        ],
    }


@app.post("/api/analyze")
def analyze(data: SensorInput):
    try:
        sensor_data = normalize_sensor_input(
            data
        )

        condition = (
            machine_condition_builder.analyze(
                sensor_data=sensor_data,
            )
        )

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

        report = generator.generate(
            machine_condition=condition,
            retrieved_documents=retrieved_documents,
        )

        report_html = markdown.markdown(
            report,
            extensions=[
                "extra",
                "nl2br",
                "sane_lists",
            ],
        )

        evidence = []

        for rank, (
            document,
            score,
        ) in enumerate(
            retrieved_documents,
            start=1,
        ):
            evidence.append(
                {
                    "rank": rank,
                    "score": round(
                        float(score),
                        4,
                    ),
                    "filename": document.metadata.get(
                        "filename",
                        "unknown",
                    ),
                    "document_type": document.metadata.get(
                        "document_type",
                        "unknown",
                    ),
                    "failure_code": document.metadata.get(
                        "failure_code",
                        "",
                    ),
                    "related_failure_codes": document.metadata.get(
                        "related_failure_codes",
                        "",
                    ),
                    "content_preview": document.page_content[
                        :500
                    ],
                }
            )

        return {
            "machine_condition": condition.to_dict(),
            "evidence": evidence,
            "report": report,
            "report_html": report_html,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


app.mount(
    "/static",
    StaticFiles(
        directory=FRONTEND_DIR
    ),
    name="static",
)


@app.get("/")
def frontend():
    return FileResponse(
        FRONTEND_DIR / "index.html"
    )