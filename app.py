import json
import time
from typing import Dict, List

import streamlit as st

from labelguard.decision_engine import verify_label
from labelguard.evidence import exportable_record
from labelguard.models import ApplicationRecord


st.set_page_config(
    page_title="LabelGuard",
    page_icon="🛡️",
    layout="wide",
)


# ---------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------

st.markdown(
    """
    <style>
        .main-title {
            font-size: 2.4rem;
            font-weight: 700;
            margin-bottom: 0.15rem;
        }

        .subtitle {
            color: #5f6368;
            font-size: 1.05rem;
            margin-bottom: 1.5rem;
        }

        .status-box {
            padding: 1rem;
            border-radius: 0.5rem;
            border: 1px solid #d0d7de;
            margin-bottom: 1rem;
        }

        .small-muted {
            color: #6b7280;
            font-size: 0.85rem;
        }

        div[data-testid="stMetric"] {
            border: 1px solid #d0d7de;
            padding: 0.75rem;
            border-radius: 0.5rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------

st.markdown(
    '<div class="main-title">🛡️ LabelGuard</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="subtitle">
        AI-assisted alcohol label verification prototype
        for compliance review workflows
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------

with st.sidebar:

    st.header("Application Record")

    application_id = st.text_input(
        "Application ID",
        value="TTB-DEMO-001",
    )

    beverage_type = st.selectbox(
        "Beverage Type",
        [
            "Distilled Spirits",
        ],
    )

    brand_name = st.text_input(
        "Brand Name",
        value="STONE'S THROW",
    )

    class_type = st.text_input(
        "Class / Type",
        value="Kentucky Straight Bourbon Whiskey",
    )

    abv = st.number_input(
        "Alcohol by Volume (%)",
        min_value=0.0,
        max_value=100.0,
        value=45.0,
        step=0.1,
    )

    net_contents_ml = st.number_input(
        "Net Contents (mL)",
        min_value=1.0,
        max_value=100000.0,
        value=750.0,
        step=1.0,
    )

    name_address = st.text_input(
        "Bottler / Producer",
        value="Stone's Throw Distillery",
    )

    country_of_origin = st.text_input(
        "Country of Origin",
        value="United States",
    )

    st.divider()

    st.caption(
        "Prototype only — no production TTB/COLA "
        "systems are connected."
    )


application = ApplicationRecord(
    application_id=application_id,
    beverage_type=beverage_type.lower().replace(
        " ",
        "_",
    ),
    brand_name=brand_name,
    class_type=class_type,
    abv=abv,
    net_contents_ml=net_contents_ml,
    name_address=name_address,
    country_of_origin=country_of_origin,
)


# ---------------------------------------------------------------------
# Main upload area
# ---------------------------------------------------------------------

st.header("1. Upload Label Images")

st.write(
    "Upload one label or a batch of labels. "
    "Each image is evaluated independently."
)

uploaded_files = st.file_uploader(
    "Choose label image files",
    type=[
        "png",
        "jpg",
        "jpeg",
        "webp",
    ],
    accept_multiple_files=True,
)

if not uploaded_files:
    st.info(
        "Start by uploading one or more label images."
    )

    st.header("How it works")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("### 1️⃣ Upload")
        st.write(
            "Submit a label image or a batch."
        )

    with col2:
        st.markdown("### 2️⃣ Read")
        st.write(
            "Local OCR extracts visible text."
        )

    with col3:
        st.markdown("### 3️⃣ Compare")
        st.write(
            "Extracted values are compared with the application."
        )

    with col4:
        st.markdown("### 4️⃣ Review")
        st.write(
            "Uncertain or conflicting results are escalated."
        )

    st.stop()


# ---------------------------------------------------------------------
# Batch controls
# ---------------------------------------------------------------------

st.header("2. Review Queue")

left, right = st.columns(
    [3, 1]
)

with left:
    st.write(
        f"**{len(uploaded_files)}** label(s) ready for verification."
    )

with right:
    run_verification = st.button(
        "Run Verification",
        type="primary",
        use_container_width=True,
    )


if run_verification:

    results: List[Dict[str, object]] = []

    progress = st.progress(
        0,
        text="Preparing verification...",
    )

    start_batch = time.perf_counter()

    for index, uploaded_file in enumerate(
        uploaded_files
    ):

        progress.progress(
            index / len(uploaded_files),
            text=(
                f"Verifying {uploaded_file.name}..."
            ),
        )

        image_bytes = uploaded_file.getvalue()

        result = verify_label(
            image_bytes=image_bytes,
            filename=uploaded_file.name,
            application=application,
        )

        evidence = exportable_record(
            application_id=application_id,
            filename=uploaded_file.name,
            result=result,
        )

        results.append(
            {
                "result": result,
                "evidence": evidence,
            }
        )

    progress.progress(
        1.0,
        text="Verification complete.",
    )

    batch_ms = int(
        (time.perf_counter() - start_batch)
        * 1000
    )

    st.session_state[
        "verification_results"
    ] = results

    st.session_state[
        "batch_ms"
    ] = batch_ms


# ---------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------

if (
    "verification_results"
    not in st.session_state
):
    st.info(
        "Click **Run Verification** to process the uploaded labels."
    )

    st.stop()


results = st.session_state[
    "verification_results"
]

batch_ms = st.session_state.get(
    "batch_ms",
    0,
)


st.header("3. Verification Results")


pass_count = sum(
    item["result"]["decision"] == "PASS"
    for item in results
)

mismatch_count = sum(
    item["result"]["decision"] == "MISMATCH"
    for item in results
)

review_count = sum(
    item["result"]["decision"] == "NEEDS_REVIEW"
    for item in results
)


metric1, metric2, metric3, metric4 = st.columns(4)

with metric1:
    st.metric(
        "Labels",
        len(results),
    )

with metric2:
    st.metric(
        "Pass",
        pass_count,
    )

with metric3:
    st.metric(
        "Mismatch",
        mismatch_count,
    )

with metric4:
    st.metric(
        "Human Review",
        review_count,
    )


st.caption(
    f"Batch processing time: {batch_ms:,} ms"
)


# ---------------------------------------------------------------------
# Individual result cards
# ---------------------------------------------------------------------

for index, item in enumerate(
    results,
    start=1,
):

    result = item["result"]
    evidence = item["evidence"]

    filename = result.get(
        "filename",
        f"Label {index}",
    )

    decision = result.get(
        "decision",
        "NEEDS_REVIEW",
    )

    processing_ms = result.get(
        "processing_ms",
        0,
    )

    ocr_confidence = result.get(
        "ocr_confidence",
        0.0,
    )

    if decision == "PASS":
        status = "🟢 PASS"

    elif decision == "MISMATCH":
        status = "🔴 MISMATCH"

    else:
        status = "🟡 NEEDS REVIEW"

    with st.expander(
        f"{status} — {filename}",
        expanded=(index == 1),
    ):

        top1, top2, top3 = st.columns(3)

        with top1:
            st.metric(
                "Decision",
                decision,
            )

        with top2:
            st.metric(
                "OCR Confidence",
                f"{ocr_confidence:.0%}",
            )

        with top3:
            st.metric(
                "Processing",
                f"{processing_ms} ms",
            )

        st.subheader(
            "Field-Level Verification"
        )

        field_rows = []

        for field in result.get(
            "fields",
            [],
        ):

            field_rows.append(
                {
                    "Field": field.get(
                        "field"
                    ),
                    "Application": field.get(
                        "application"
                    ),
                    "Observed": field.get(
                        "observed"
                    ),
                    "Decision": field.get(
                        "decision"
                    ),
                    "Confidence": (
                        f"{float(field.get('confidence', 0)):.0%}"
                    ),
                }
            )

        if field_rows:
            st.dataframe(
                field_rows,
                use_container_width=True,
                hide_index=True,
            )

        st.subheader(
            "Why?"
        )

        for message in evidence.get(
            "summary",
            [],
        ):
            st.write(
                f"• {message}"
            )

        review_flags = result.get(
            "review_flags",
            [],
        )

        if review_flags:
            st.warning(
                "Human-review flags detected."
            )

            for flag in review_flags:
                st.write(
                    f"⚠️ {flag}"
                )

        with st.expander(
            "OCR Evidence"
        ):

            st.text(
                result.get(
                    "extracted_text",
                    "",
                )
            )

        with st.expander(
            "Machine-Readable Decision Trace"
        ):

            st.json(
                evidence
            )


# ---------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------

st.header("4. Export Results")

export_payload = {
    "application": {
        "application_id": application.application_id,
        "beverage_type": application.beverage_type,
        "brand_name": application.brand_name,
        "class_type": application.class_type,
        "abv": application.abv,
        "net_contents_ml": application.net_contents_ml,
        "name_address": application.name_address,
        "country_of_origin": application.country_of_origin,
    },
    "batch_processing_ms": batch_ms,
    "results": [
        item["evidence"]
        for item in results
    ],
}

json_payload = json.dumps(
    export_payload,
    indent=2,
    default=str,
)

st.download_button(
    "Download Verification Evidence (JSON)",
    data=json_payload,
    file_name="labelguard_verification.json",
    mime="application/json",
    use_container_width=True,
)


# ---------------------------------------------------------------------
# Prototype limitations
# ---------------------------------------------------------------------

st.divider()

with st.expander(
    "Prototype Scope & Limitations"
):

    st.markdown(
        """
        **This prototype is decision support, not an automated
        legal determination.**

        - OCR results can contain errors.
        - Textual presence does not prove visual typography.
        - Government-warning formatting requires human verification.
        - The prototype does not connect to COLA.
        - No production records are stored.
        - The current rules focus on distilled-spirit examples.
        - Low-confidence results are intentionally escalated.
        - Production deployment would require appropriate federal
          security, privacy, retention, accessibility, and
          authorization controls.
        """
    )
