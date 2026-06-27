"""
Response schemas — structured Pydantic v2 models for the MedicalReport.

The MedicalReport is the core API response type. It contains all
10 clinical sections required by the specification, plus metadata.
Every field is typed so the OpenAPI schema is fully self-documented.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Sub-models
# ─────────────────────────────────────────────────────────────────────────────

class ContributingFactor(BaseModel):
    """A single medical indicator that influenced the prediction."""

    name: str = Field(..., description="Name of the medical indicator.")
    value: str = Field(..., description="Patient's recorded value.")
    normal_range: str = Field(..., description="Typical normal reference range.")
    status: Literal["Normal", "Borderline", "Abnormal"] = Field(
        ..., description="Whether the value is within, near, or outside normal range."
    )
    interpretation: str = Field(..., description="Clinical meaning of this value.")


class LifestyleRecommendations(BaseModel):
    """Personalised lifestyle guidance based on patient inputs."""

    diet: list[str] = Field(default_factory=list, description="Dietary recommendations.")
    physical_activity: list[str] = Field(
        default_factory=list, description="Exercise and movement recommendations."
    )
    sleep: list[str] = Field(default_factory=list, description="Sleep hygiene tips.")
    weight_management: list[str] = Field(
        default_factory=list, description="Weight-related advice."
    )
    hydration: list[str] = Field(default_factory=list, description="Hydration guidance.")
    stress_management: list[str] = Field(
        default_factory=list, description="Mental health and stress reduction tips."
    )
    smoking: list[str] = Field(
        default_factory=list, description="Smoking cessation advice if applicable."
    )
    alcohol: list[str] = Field(
        default_factory=list, description="Alcohol consumption guidance if applicable."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Core Response Model
# ─────────────────────────────────────────────────────────────────────────────

class MedicalReport(BaseModel):
    """
    Comprehensive AI-generated medical risk assessment report.

    This is the primary response body returned by every prediction endpoint.
    It mirrors a physician's consultation report with 10 structured sections.
    """

    # ── Metadata ───────────────────────────────────────────────────────────
    disease_name: str = Field(
        ..., description="Human-readable name of the screened condition."
    )
    specialist_role: str = Field(
        ..., description="The type of medical specialist relevant to this disease."
    )
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of report generation.",
    )
    model_version: str = Field(
        default="2.0.0", description="Version of the prediction model used."
    )

    # ── Section 1 — Prediction Summary ─────────────────────────────────────
    prediction_label: str = Field(
        ..., description="The model's primary classification (e.g. Malignant / Benign)."
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model confidence as a value between 0 and 1.",
    )
    risk_level: Literal["Low", "Moderate", "High"] = Field(
        ..., description="Categorised risk level derived from prediction and confidence."
    )
    prediction_summary: str = Field(
        ..., description="One-paragraph executive summary of the prediction result."
    )

    # ── Section 2 — Explanation ────────────────────────────────────────────
    explanation: str = Field(
        ...,
        description=(
            "Plain-language explanation of why the model reached this conclusion "
            "and which factors drove the decision."
        ),
    )

    # ── Section 3 — Clinical Interpretation ────────────────────────────────
    clinical_interpretation: str = Field(
        ...,
        description=(
            "Specialist-level interpretation of the patient's values and findings, "
            "written in an empathetic, consultation-style tone."
        ),
    )
    contributing_factors: list[ContributingFactor] = Field(
        default_factory=list,
        description="Breakdown of each significant medical indicator.",
    )

    # ── Section 4 — Lifestyle Recommendations ──────────────────────────────
    lifestyle_recommendations: LifestyleRecommendations = Field(
        default_factory=LifestyleRecommendations,
        description="Personalised lifestyle guidance.",
    )

    # ── Section 5 — Do's ───────────────────────────────────────────────────
    dos: list[str] = Field(
        default_factory=list,
        description="Personalised list of recommended actions.",
    )

    # ── Section 6 — Don'ts ─────────────────────────────────────────────────
    donts: list[str] = Field(
        default_factory=list,
        description="Personalised list of actions to avoid.",
    )

    # ── Section 7 — When to See a Doctor ───────────────────────────────────
    when_to_see_doctor: str = Field(
        ...,
        description=(
            "Guidance on consultation urgency, follow-up tests, and warning "
            "symptoms that require emergency care."
        ),
    )

    # ── Section 8 — Preventive Care ────────────────────────────────────────
    preventive_care: list[str] = Field(
        default_factory=list,
        description="Long-term screening and preventive health recommendations.",
    )

    # ── Section 9 — In Simple Words ────────────────────────────────────────
    in_simple_words: str = Field(
        ...,
        description=(
            "Patient-friendly explanation in everyday language, free of medical jargon."
        ),
    )

    # ── Section 10 — Disclaimer ────────────────────────────────────────────
    disclaimer: str = Field(
        default=(
            "⚠️ This AI-generated report is intended for educational and screening "
            "purposes only. It is NOT a substitute for professional medical advice, "
            "diagnosis, or treatment. The predictions reflect statistical risk patterns "
            "and cannot definitively confirm or rule out any medical condition. "
            "Always consult a qualified and licensed healthcare professional before "
            "making any medical decisions. In the case of a medical emergency, "
            "contact emergency services immediately."
        ),
        description="Standard medical disclaimer appended to every report.",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Error Response
# ─────────────────────────────────────────────────────────────────────────────

class ErrorDetail(BaseModel):
    """Structured error response body."""

    error: str = Field(..., description="Short error type identifier.")
    message: str = Field(..., description="Human-readable description of the error.")
    request_id: str | None = Field(None, description="Request ID for tracing.")


class HealthResponse(BaseModel):
    """Health check response."""

    status: Literal["healthy", "degraded"] = "healthy"
    version: str
    uptime_seconds: float
    loaded_models: list[str]
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
