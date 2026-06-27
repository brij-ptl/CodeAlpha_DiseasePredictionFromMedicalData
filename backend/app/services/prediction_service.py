"""
Prediction Service.

Orchestrates the full prediction pipeline:
  1. Load model + scaler from the registry
  2. Build a pandas DataFrame from validated input
  3. Scale the features
  4. Run inference (predict + predict_proba)
  5. Derive the risk level
  6. Delegate report generation to the report service
  7. Return the completed MedicalReport

This is the only place in the codebase that touches ML inference logic.
"""

from __future__ import annotations

from typing import Literal

import pandas as pd

from app.models.registry import ModelNotFoundError, model_registry
from app.schemas.responses import MedicalReport
from app.services.report_service import get_report_generator
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

RiskLevel = Literal["Low", "Moderate", "High"]

# ─────────────────────────────────────────────────────────────────────────────
# Disease-specific prediction metadata
# ─────────────────────────────────────────────────────────────────────────────

#: Maps disease key → (positive_label, negative_label, positive_class_index)
#: positive_class_index is the index in predict_proba that represents "risk".
_DISEASE_META: dict[str, tuple[str, str, int]] = {
    "breast-cancer": ("Malignant", "Benign", 0),
    "diabetes":      ("Positive",  "Negative", 1),
    "heart-disease": ("Presence",  "Absence",  1),
}


# ─────────────────────────────────────────────────────────────────────────────
# Risk level derivation
# ─────────────────────────────────────────────────────────────────────────────

def _derive_risk_level(is_positive: bool, confidence: float) -> RiskLevel:
    """
    Map prediction outcome + confidence → risk level.

    Rules:
      - Negative prediction → Low risk regardless of confidence
      - Positive + confidence < 0.60 → Moderate risk
      - Positive + confidence >= 0.60 → High risk
    """
    if not is_positive:
        return "Low"
    return "High" if confidence >= 0.60 else "Moderate"


# ─────────────────────────────────────────────────────────────────────────────
# Main prediction function
# ─────────────────────────────────────────────────────────────────────────────

def run_prediction(disease_key: str, feature_dict: dict[str, float]) -> MedicalReport:
    """
    Execute the full prediction and report generation pipeline.

    Args:
        disease_key:  URL slug identifying the disease (e.g. "breast-cancer").
        feature_dict: Dictionary mapping feature names to patient values.
                      The key names MUST match those used during model training.

    Returns:
        A fully-populated MedicalReport instance.

    Raises:
        ModelNotFoundError: If model files are not present on disk.
        ValueError:         If the disease key is not registered.
        RuntimeError:       If inference fails unexpectedly.
    """
    logger.info("Running prediction for disease='%s'", disease_key)

    # 1. Validate disease key
    if disease_key not in _DISEASE_META:
        raise ValueError(
            f"Unknown disease key '{disease_key}'. "
            f"Supported: {list(_DISEASE_META.keys())}"
        )

    pos_label, neg_label, pos_class_idx = _DISEASE_META[disease_key]

    # 2. Load model + scaler (lazy, cached)
    try:
        model, scaler = model_registry.get(disease_key)
    except ModelNotFoundError:
        raise
    except Exception as exc:
        raise RuntimeError(
            f"Unexpected error loading model for '{disease_key}': {exc}"
        ) from exc

    # 3. Build feature DataFrame preserving column order
    feature_names = list(feature_dict.keys())
    df = pd.DataFrame([feature_dict], columns=feature_names)

    # 4. Scale features
    X_scaled = scaler.transform(df)

    # 5. Inference
    raw_pred = int(model.predict(X_scaled)[0])
    proba = model.predict_proba(X_scaled)[0]

    # Confidence is the probability assigned to the predicted class
    confidence = float(proba[raw_pred])

    # Determine label
    is_positive = (raw_pred == pos_class_idx)
    prediction_label = pos_label if is_positive else neg_label

    logger.info(
        "Prediction result: disease='%s' label='%s' confidence=%.4f",
        disease_key,
        prediction_label,
        confidence,
    )

    # 6. Derive risk level
    risk_level: RiskLevel = _derive_risk_level(is_positive, confidence)

    # 7. Generate comprehensive medical report
    generator = get_report_generator(disease_key)
    report = generator.generate(
        inputs=feature_dict,
        prediction_label=prediction_label,
        confidence=confidence,
        risk_level=risk_level,
    )

    logger.info("Report generated successfully for disease='%s'", disease_key)
    return report
