"""
Request schemas — validated Pydantic v2 models for all disease inputs.

Each model includes:
  • Type annotations
  • Field-level constraints (ge/le bounds)
  • Descriptive metadata for OpenAPI documentation
  • A .to_feature_dict() helper consumed by the prediction service
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


# ─────────────────────────────────────────────────────────────────────────────
# Breast Cancer
# ─────────────────────────────────────────────────────────────────────────────

class BreastCancerRequest(BaseModel):
    """
    Cytological features from a Fine Needle Aspirate (FNA) biopsy.
    Values are computed from digitised images of cell nuclei.
    """

    mean_radius: float = Field(
        ...,
        ge=5.0,
        le=30.0,
        description="Mean of distances from center to points on the perimeter (mm).",
        json_schema_extra={"example": 14.13},
    )
    mean_texture: float = Field(
        ...,
        ge=5.0,
        le=40.0,
        description="Standard deviation of grey-scale values — measures texture irregularity.",
        json_schema_extra={"example": 19.27},
    )
    mean_perimeter: float = Field(
        ...,
        ge=40.0,
        le=200.0,
        description="Mean perimeter of the cell nucleus (mm).",
        json_schema_extra={"example": 91.98},
    )
    mean_area: float = Field(
        ...,
        ge=100.0,
        le=2600.0,
        description="Mean area of the cell nucleus (mm²).",
        json_schema_extra={"example": 654.9},
    )
    mean_smoothness: float = Field(
        ...,
        ge=0.05,
        le=0.20,
        description="Mean local variation in radius lengths — measures smoothness.",
        json_schema_extra={"example": 0.0987},
    )

    def to_feature_dict(self) -> dict[str, float]:
        return {
            "mean radius": self.mean_radius,
            "mean texture": self.mean_texture,
            "mean perimeter": self.mean_perimeter,
            "mean area": self.mean_area,
            "mean smoothness": self.mean_smoothness,
        }

    model_config = {
        "json_schema_extra": {
            "example": {
                "mean_radius": 14.13,
                "mean_texture": 19.27,
                "mean_perimeter": 91.98,
                "mean_area": 654.9,
                "mean_smoothness": 0.0987,
            }
        }
    }


# ─────────────────────────────────────────────────────────────────────────────
# Diabetes
# ─────────────────────────────────────────────────────────────────────────────

class DiabetesRequest(BaseModel):
    """
    Metabolic and demographic markers used for Type 2 Diabetes risk assessment.
    Based on the Pima Indians Diabetes Dataset (NIDDK).
    """

    pregnancies: float = Field(
        ...,
        ge=0,
        le=20,
        description="Number of times the patient has been pregnant.",
        json_schema_extra={"example": 2},
    )
    glucose: float = Field(
        ...,
        ge=44.0,
        le=300.0,
        description="Plasma glucose concentration (mg/dL) — 2-hour oral glucose tolerance test.",
        json_schema_extra={"example": 120.0},
    )
    blood_pressure: float = Field(
        ...,
        ge=30.0,
        le=130.0,
        description="Diastolic blood pressure (mmHg).",
        json_schema_extra={"example": 72.0},
    )
    bmi: float = Field(
        ...,
        ge=10.0,
        le=70.0,
        description="Body Mass Index (weight in kg / height in m²).",
        json_schema_extra={"example": 27.5},
    )
    age: float = Field(
        ...,
        ge=18,
        le=120,
        description="Patient age in years.",
        json_schema_extra={"example": 35},
    )

    def to_feature_dict(self) -> dict[str, float]:
        return {
            "Pregnancies": self.pregnancies,
            "Glucose": self.glucose,
            "BloodPressure": self.blood_pressure,
            "BMI": self.bmi,
            "Age": self.age,
        }

    model_config = {
        "json_schema_extra": {
            "example": {
                "pregnancies": 2,
                "glucose": 120.0,
                "blood_pressure": 72.0,
                "bmi": 27.5,
                "age": 35,
            }
        }
    }


# ─────────────────────────────────────────────────────────────────────────────
# Heart Disease
# ─────────────────────────────────────────────────────────────────────────────

class HeartDiseaseRequest(BaseModel):
    """
    Cardiac indicators derived from the UCI Cleveland Heart Disease Dataset.
    """

    age: float = Field(
        ...,
        ge=18,
        le=100,
        description="Patient age in years.",
        json_schema_extra={"example": 54},
    )
    sex: float = Field(
        ...,
        ge=0,
        le=1,
        description="Biological sex: 1 = Male, 0 = Female.",
        json_schema_extra={"example": 1},
    )
    cp: float = Field(
        ...,
        ge=1,
        le=4,
        description=(
            "Chest pain type: 1 = Typical angina, 2 = Atypical angina, "
            "3 = Non-anginal pain, 4 = Asymptomatic."
        ),
        json_schema_extra={"example": 2},
    )
    trestbps: float = Field(
        ...,
        ge=80.0,
        le=220.0,
        description="Resting blood pressure (mmHg) on admission to hospital.",
        json_schema_extra={"example": 130.0},
    )
    chol: float = Field(
        ...,
        ge=100.0,
        le=600.0,
        description="Serum cholesterol (mg/dL) — total cholesterol from blood test.",
        json_schema_extra={"example": 240.0},
    )

    @model_validator(mode="after")
    def validate_cp_integer(self) -> "HeartDiseaseRequest":
        """Chest pain type must be a whole number (1–4)."""
        if self.cp not in (1.0, 2.0, 3.0, 4.0):
            raise ValueError("cp must be an integer between 1 and 4.")
        return self

    def to_feature_dict(self) -> dict[str, float]:
        return {
            "age": self.age,
            "sex": self.sex,
            "cp": self.cp,
            "trestbps": self.trestbps,
            "chol": self.chol,
        }

    model_config = {
        "json_schema_extra": {
            "example": {
                "age": 54,
                "sex": 1,
                "cp": 2,
                "trestbps": 130.0,
                "chol": 240.0,
            }
        }
    }
