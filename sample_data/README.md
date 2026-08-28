# Sample Test Data

This directory is reserved for non-sensitive test images used to
evaluate the LabelGuard prototype.

## Purpose

Sample labels can be used to test:

- OCR extraction
- Brand-name matching
- Class/type matching
- ABV matching
- Net-content matching
- Government-warning detection
- Mismatch detection
- Human-review escalation
- Batch processing

## Test Scenarios

The prototype is designed to support at least these scenarios:

### 1. Matching label

The label contains values that correspond to the application record.

Expected outcome:

`PASS` or `NEEDS_REVIEW`

A `NEEDS_REVIEW` result is acceptable when the textual checks succeed
but visual requirements require human confirmation.

### 2. Brand mismatch

The application and label contain different brand names.

Expected outcome:

`MISMATCH`

### 3. ABV mismatch

The application and label contain different alcohol-by-volume values.

Expected outcome:

`MISMATCH`

### 4. Net-content mismatch

The application and label contain different net contents.

Expected outcome:

`MISMATCH`

### 5. Missing warning

The label does not contain the expected government warning.

Expected outcome:

`MISMATCH`

### 6. Low-quality image

The image has poor OCR quality.

Expected outcome:

`NEEDS_REVIEW`

### 7. Batch upload

Multiple label images are uploaded simultaneously.

Expected behavior:

Each label receives an independent verification result.

## Data Handling

No production TTB records, personally identifiable information,
or confidential government information should be placed in this
directory.

All test images should be synthetic, publicly available, or otherwise
authorized for use in the prototype.
