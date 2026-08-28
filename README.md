# LabelGuard

## AI-Assisted Alcohol Label Verification Prototype

LabelGuard is a standalone proof-of-concept designed to assist alcohol beverage compliance agents by automatically comparing information extracted from a label image against an application record.

The prototype focuses on a simple principle:

> Automate routine comparison work while keeping uncertain compliance decisions in the hands of a human reviewer.

LabelGuard does not connect to TTB's COLA system and does not make a legal determination of compliance.

---

## Project Overview

Compliance agents routinely compare information appearing on alcohol beverage labels with information submitted in an application.

Examples include:

- Brand name
- Class/type designation
- Alcohol by volume
- Net contents
- Bottler/producer information
- Country of origin
- Government warning statement

The prototype uses local OCR and deterministic comparison logic to identify potential matches, mismatches, and situations requiring human review.

The architecture intentionally avoids dependence on external AI APIs for the core verification workflow.

---

# Key Design Goals

## 1. Fast feedback

The stakeholder requirement calls for results in approximately five seconds or less.

The prototype therefore uses local OCR rather than making every verification dependent on an external cloud AI service.

Actual performance depends on:

- Image resolution
- Image complexity
- OCR processing time
- Hardware
- Number of uploaded labels

The application displays processing time so the prototype can be evaluated against the performance requirement.

---

## 2. Simple user experience

The interface is designed for users with widely varying levels of technical experience.

The workflow is intentionally simple:

1. Enter the application information.
2. Upload one or more label images.
3. Click **Run Verification**.
4. Review the results.
5. Examine evidence when necessary.
6. Export the verification record.

---

## 3. Batch processing

Multiple label images can be uploaded at the same time.

Each image receives an independent result.

This supports scenarios in which an importer submits a large number of applications together.

---

## 4. Human-in-the-loop verification

LabelGuard does not attempt to replace the compliance agent.

Results are categorized as:

### PASS

The automated checks found matching evidence and no unresolved review conditions.

### MISMATCH

The system identified a material difference between the application record and observed label information.

### NEEDS_REVIEW

The system could not establish sufficient evidence for an automatic conclusion.

Examples include:

- Low OCR confidence
- Missing text
- Warning text requiring visual inspection
- Uncertain extraction
- Processing errors

This conservative approach is intentional.

---

# Architecture

```text
                    ┌─────────────────────┐
                    │     Streamlit UI    │
                    │       app.py        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Decision Engine   │
                    │ decision_engine.py  │
                    └──────────┬──────────┘
                               │
                 ┌─────────────┼─────────────┐
                 ▼             ▼             ▼
          ┌────────────┐ ┌────────────┐ ┌──────────────┐
          │    OCR     │ │ Extraction │ │ Normalization│
          │   Layer    │ │   Layer    │ │    Layer     │
          └────────────┘ └────────────┘ └──────────────┘
                 │             │             │
                 └─────────────┼─────────────┘
                               ▼
                    ┌─────────────────────┐
                    │ Compliance Rules    │
                    │      rules/         │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Evidence / Audit    │
                    │      Layer          │
                    └─────────────────────┘
