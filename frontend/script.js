const el = (id) =>
    document.getElementById(id);


const inputs = {
    type: el("type"),

    air: el(
        "air_temperature"
    ),

    process: el(
        "process_temperature"
    ),

    rpm: el(
        "rotational_speed"
    ),

    torque: el(
        "torque"
    ),

    wear: el(
        "tool_wear"
    ),
};


const sampleButton =
    el("sample-btn");

const analyzeButton =
    el("analyze-btn");

const errorBox =
    el("error-box");


function showError(
    message
) {

    errorBox.textContent =
        message;

    errorBox.classList.remove(
        "hidden"
    );
}


function clearError() {

    errorBox.textContent =
        "";

    errorBox.classList.add(
        "hidden"
    );
}


function setLoading(
    isLoading
) {

    sampleButton.disabled =
        isLoading;

    analyzeButton.disabled =
        isLoading;

    analyzeButton.textContent =
        isLoading
            ? "Analyzing..."
            : "Analyze Machine";
}


function readInput() {

    return {

        type:
            inputs.type.value,

        air_temperature:
            Number(
                inputs.air.value
            ),

        process_temperature:
            Number(
                inputs.process.value
            ),

        rotational_speed:
            Number(
                inputs.rpm.value
            ),

        torque:
            Number(
                inputs.torque.value
            ),

        tool_wear:
            Number(
                inputs.wear.value
            ),
    };
}


function populateSample(
    data
) {

    inputs.type.value =
        data.type;

    inputs.air.value =
        data.air_temperature;

    inputs.process.value =
        data.process_temperature;

    inputs.rpm.value =
        data.rotational_speed;

    inputs.torque.value =
        data.torque;

    inputs.wear.value =
        data.tool_wear;
}


function renderCondition(
    condition
) {

    const status =
        condition.status
            .toLowerCase();


    el(
        "system-status"
    ).textContent =
        condition.status;


    const statusElement =
        el("criticality");


    statusElement.textContent =
        condition.status;


    statusElement.className =
        `criticality ${status}`;


    el(
        "diagnosis"
    ).textContent =
        condition.diagnosis;


    const p =
        Math.max(
            0,
            Math.min(
                100,
                Number(
                    condition.failure_probability
                ) * 100
            )
        );


    el(
        "failure-probability"
    ).textContent =
        `${p.toFixed(1)}%`;


    el(
        "probability-bar"
    ).style.width =
        `${p}%`;


    const sensors =
        condition.sensor_state;


    el(
        "sensor-air"
    ).textContent =
        `${sensors["Air temperature [K]"]} K`;


    el(
        "sensor-process"
    ).textContent =
        `${sensors["Process temperature [K]"]} K`;


    el(
        "sensor-rpm"
    ).textContent =
        `${sensors["Rotational speed [rpm]"]} RPM`;


    el(
        "sensor-torque"
    ).textContent =
        `${sensors["Torque [Nm]"]} Nm`;


    el(
        "sensor-wear"
    ).textContent =
        `${sensors["Tool wear [min]"]} min`;


    renderFaults(
        condition.fault_candidates ||
        []
    );
}


function renderFaults(
    candidates
) {

    if (
        !candidates.length
    ) {

        el(
            "fault-list"
        ).innerHTML =
            `
            <div class="empty-state">
                No fault candidates.
            </div>
            `;

        return;
    }


    el(
        "fault-list"
    ).innerHTML =
        candidates.map(
            (
                candidate
            ) => {

                const p =
                    Math.max(
                        0,
                        Math.min(
                            100,
                            Number(
                                candidate.probability
                            ) * 100
                        )
                    );


                return `
                <div class="fault-item">

                    <div class="fault-top">

                        <span class="fault-name">
                            ${escapeHtml(
                                candidate.fault
                            )}
                        </span>

                        <span class="fault-probability">
                            ${p.toFixed(1)}%
                        </span>

                    </div>


                    <div class="fault-bar">

                        <div
                            class="fault-bar-fill"
                            style="width: ${p}%"
                        ></div>

                    </div>

                </div>
                `;

            }
        ).join("");
}


function renderEvidence(
    evidence
) {

    el(
        "evidence-count"
    ).textContent =
        `${evidence.length} SOURCES`;


    if (
        !evidence.length
    ) {

        el(
            "evidence-list"
        ).innerHTML =
            `
            <div class="empty-state">
                No evidence retrieved.
            </div>
            `;

        return;
    }


    el(
        "evidence-list"
    ).innerHTML =
        evidence.map(
            (
                item
            ) => {

                const meta = [
                    item.document_type ||
                        "unknown",

                    item.failure_code ||
                        null,

                ]
                    .filter(Boolean)
                    .join(" · ");


                return `
                <div class="evidence-item">

                    <div class="evidence-top">

                        <span class="evidence-source">

                            [${item.rank}]
                            ${escapeHtml(
                                item.filename
                            )}

                        </span>


                        <span class="score">

                            ${Number(
                                item.score
                            ).toFixed(4)}

                        </span>

                    </div>


                    <div class="evidence-meta">

                        ${escapeHtml(
                            meta
                        )}

                    </div>


                    <div class="evidence-preview">

                        ${escapeHtml(
                            item.content_preview
                        )}

                    </div>

                </div>
                `;

            }
        ).join("");
}


function renderReport(
    html
) {

    el(
        "report"
    ).innerHTML =
        html ||
        `
        <div class="empty-state">
            No report generated.
        </div>
        `;
}


async function loadSample() {

    clearError();


    try {

        const response =
            await fetch(
                "/api/sample"
            );


        const data =
            await response.json();


        if (
            !response.ok
        ) {

            throw new Error(
                data.detail ||
                "Failed to load sample."
            );

        }


        populateSample(
            data
        );

    } catch (
        error
    ) {

        showError(
            error.message
        );
    }
}


async function analyze() {

    clearError();

    setLoading(
        true
    );


    try {

        const response =
            await fetch(
                "/api/analyze",
                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json",
                    },

                    body:
                        JSON.stringify(
                            readInput()
                        ),
                }
            );


        const data =
            await response.json();


        if (
            !response.ok
        ) {

            throw new Error(
                data.detail ||
                "Analysis failed."
            );

        }


        renderCondition(
            data.machine_condition
        );


        renderEvidence(
            data.evidence
        );


        renderReport(
            data.report_html
        );

    } catch (
        error
    ) {

        showError(
            error.message
        );

    } finally {

        setLoading(
            false
        );
    }
}


function escapeHtml(
    value
) {

    return String(
        value ?? ""
    )
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );
}


sampleButton.addEventListener(
    "click",
    loadSample
);


analyzeButton.addEventListener(
    "click",
    analyze
);