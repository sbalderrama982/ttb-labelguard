import json
import time
from concurrent.futures import ThreadPoolExecutor

import streamlit as st

from labelguard.decision_engine import verify_label
from labelguard.models import ApplicationRecord


st.set_page_config(
    page_title="LabelGuard | TTB",
    page_icon="🛡️",
    layout="wide",
)


st.markdown(
    """
    <style>
        .main-title {
            font-size: 2.4rem;
            font-weight: 800;
            margin-bottom: 0;
        }

        .subtitle {
            color: #667085;
            font-size: 1rem;
            margin-bottom: 2rem;
        }

        .decision-pass {
            background: #e8f7ee;
            border-left: 6px solid #16834a;
            padding: 1rem;
            border-radius: 8px;
        }

        .decision-mismatch {
            background: #fff0ef;
            border-left: 6px solid #c62828;
            padding: 1rem;
            border-radius: 8px;
        }

        .decision-review {
            background: #fff8e1;
            border-left: 6px solid #d28b00;
            padding: 1rem;
            border-radius: 8px;
        }

        .small-muted {
            color: #667085;
            font-size: .85rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def application_form():
    st.subheader("Application Record")

    col1, col2 = st.columns(2)

    with col1:
        application_id = st.text_input(
            "Application ID",
            value="TTB-DEMO-1042",
        )

        brand_name = st.text_input(
            "Brand Name",
            value="Stone's Throw",
        )

        class_type = st.text_input(
            "Class / Type",
            value="Kentucky Straight Bourbon Whiskey",
        )

        name_address = st.text_input(
            "Bottler / Producer",
            value="Stone's Throw Distillery, Frankfort, KY",
        )

    with col2:
        abv = st.number_input(
            "Alcohol by Volume (%)",
            min_value=0.0,
            max_value=100.0,
            value=45.0,
            step=0.1,
        )

        net_contents_ml = st.number_input(
            "Net Contents (mL)",
            min_value=0.0,
            value=750.0,
            step=1.0,
        )

        country_of_origin = st.text_input(
            "Country of Origin",
            value="United States",
        )

    return ApplicationRecord(
        application_id=application_id,
        beverage_type="distilled_spirits",
        brand_name=brand_name,
        class_type=class_type,
        abv=abv,
        net_contents_ml=net_contents_ml,
        name_address=name_address,
        country_of_origin=country_of_origin,
    )


def render_result(result):
    decision = result["decision"]

    if decision == "PASS":
        css_class = "decision-pass"
        icon = "🟢"
    elif decision == "MISMATCH":
        css_class = "decision-mismatch"
        icon = "🔴"
    else:
        css_class = "decision-review"
        icon = "🟡"

    st.markdown(
        f"""
        <div class="{css_class}">
            <h3>{icon} {decision.replace("_", " ")}</h3>
            <div class="small-muted">
                {result["filename"]} ·
                {result["processing_ms"]} ms ·
                OCR confidence: {result["ocr_confidence"]:.0%}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    rows = []

    for field in result["fields"]:
        rows.append(
            {
                "Field": field["field"],
                "Application": field.get("application") or "—",
                "Observed": field.get("observed") or "—",
                "Decision": field["decision"],
                "Confidence": f'{field["confidence"]:.0%}',
                "Reason": field["reason"],
            }
        )

    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
    )

    if result["review_flags"]:
        with st.expander("Human-review checks"):
            for flag in result["review_flags"]:
                st.write(f"• {flag}")

    with st.expander("Evidence / OCR text"):
        st.code(result["extracted_text"] or "[No OCR text detected]")

        st.json(result["trace"])


def main():
    st.markdown(
        '<div class="main-title">🛡️ LabelGuard</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="subtitle">
            AI-assisted alcohol label verification for TTB compliance workflows.
            Evidence first. Human judgment when evidence is uncertain.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("About LabelGuard")

        st.write(
            """
            LabelGuard is a prototype designed to reduce repetitive
            label-to-application matching while keeping compliance
            agents in the decision loop.
            """
        )

        st.divider()

        st.caption("Prototype architecture")
        st.write(
            """
            1. Image preparation  
            2. OCR / vision  
            3. Evidence extraction  
            4. Normalization  
            5. Rule evaluation  
            6. Human-review gate
            """
        )

        st.divider()

        st.caption(
            "This prototype does not replace an authorized TTB compliance determination."
        )

    application = application_form()

    st.divider()

    st.subheader("Label Images")

    uploaded_files = st.file_uploader(
        "Upload one or more alcohol label images",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        help="Batch uploads are supported for importer submissions.",
    )

    if uploaded_files:
        st.info(
            f"{len(uploaded_files)} label(s) selected."
        )

        with st.expander("Selected files"):
            for file in uploaded_files:
                st.write(
                    f"• {file.name} — "
                    f"{file.size / 1024:.1f} KB"
                )

    verify_button = st.button(
        "🔎 Run Label Verification",
        type="primary",
        use_container_width=True,
        disabled=not uploaded_files,
    )

    if verify_button:
        results = []

        progress = st.progress(0)

        start_time = time.perf_counter()

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []

            for file in uploaded_files:
                futures.append(
                    executor.submit(
                        verify_label,
                        file.getvalue(),
                        file.name,
                        application,
                    )
                )

            for index, future in enumerate(futures, start=1):
                try:
                    results.append(future.result())
                except Exception as exc:
                    results.append(
                        {
                            "filename": uploaded_files[index - 1].name,
                            "decision": "NEEDS_REVIEW",
                            "processing_ms": 0,
                            "ocr_confidence": 0,
                            "fields": [],
                            "review_flags": [
                                f"Processing error: {exc}"
                            ],
                            "extracted_text": "",
                            "trace": [],
                        }
                    )

                progress.progress(
                    index / len(futures)
                )

        elapsed = time.perf_counter() - start_time

        st.session_state["results"] = results
        st.session_state["batch_elapsed"] = elapsed

    if "results" in st.session_state:
        results = st.session_state["results"]

        st.divider()
        st.header("Verification Results")

        pass_count = sum(
            r["decision"] == "PASS"
            for r in results
        )

        mismatch_count = sum(
            r["decision"] == "MISMATCH"
            for r in results
        )

        review_count = sum(
            r["decision"] == "NEEDS_REVIEW"
            for r in results
        )

        processing_times = [
            r["processing_ms"]
            for r in results
            if r["processing_ms"] > 0
        ]

        average_ms = (
            sum(processing_times) / len(processing_times)
            if processing_times
            else 0
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("PASS", pass_count)
        c2.metric("MISMATCH", mismatch_count)
        c3.metric("NEEDS REVIEW", review_count)
        c4.metric(
            "Avg. Processing",
            f"{average_ms:.0f} ms",
        )

        st.caption(
            f"Batch wall-clock time: "
            f"{st.session_state.get('batch_elapsed', 0):.2f} seconds"
        )

        for result in results:
            st.write("")
            render_result(result)


if __name__ == "__main__":
    main()
