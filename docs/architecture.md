# Architecture & Verification Methodology

## Core System Architecture

```
                  ┌──────────────────────┐
                  │      Input PDF       │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Universal Extractor  │
                  │  (pypdf + regex)     │
                  └──────────┬───────────┘
                             │
                    Source Sentences JSON
                             │
                             ▼
                  ┌──────────────────────┐
                  │ AI Agent / Translator│
                  │ (Zero-Omission Prmpt)│
                  └──────────┬───────────┘
                             │
                     Target Markdown
                             │
                             ▼
                  ┌──────────────────────┐
                  │ MultiLingual Verifier│
                  │ (Sentence Delimiters)│
                  └──────────┬───────────┘
                             │
                  Pass/Fail Status & Ratio
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
    [VERIFIED (Ratio >= 1.0)]      [FLAGGED (Ratio < 0.8)]
              │                             │
              ▼                             ▼
    Record to Tracker               Loop back & Fix
```

## Mathematical Model of Verification
Let $S_{src}$ be the set of segmented source sentences on page $P$:
$$N_{src} = |S_{src}|$$

Let $S_{target}$ be the set of segmented translated sentences on page $P$:
$$N_{target} = |S_{target}|$$

The **Sentence Coverage Ratio** $R$ is defined as:
$$R = \frac{N_{target}}{N_{src}}$$

### Verification Criteria:
1. **Pass (VERIFIED)**: $N_{target} \ge \max(1, \lfloor 0.8 \times N_{src} \rfloor)$ and $R \ge 1.0$ (for expressive literary and explanatory target languages).
2. **Flagged (FLAGGED_INCOMPLETE)**: $N_{target} < 0.8 \times N_{src}$, indicating that clauses or sentences were merged or skipped.
