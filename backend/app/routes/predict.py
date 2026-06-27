"""
Prediction routes — v1.

Three POST endpoints, one per supported disease.
All endpoints follow the same pattern:
  1. Accept a validated Pydantic request body
  2. Convert to a feature dict
  3. Call prediction_service.run_prediction()
  4. Return a structured MedicalReport JSON response

Error handling:
  - 422: Validation errors (Pydantic, automatic)
  - 503: Model not found / not trained
  - 500: Unexpected inference error
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.models.registry import ModelLoadError, ModelNotFoundError
from app.schemas.requests import (
    BreastCancerRequest,
    DiabetesRequest,
    HeartDiseaseRequest,
)
from app.schemas.responses import ErrorDetail, MedicalReport
from app.services.prediction_service import run_prediction
from app.utils.logging_config import get_logger, request_id_ctx

logger = get_logger(__name__)

router = APIRouter(
    prefix="/predict",
    tags=["Predictions"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Shared error handler
# ─────────────────────────────────────────────────────────────────────────────

def _handle_prediction_error(disease_key: str, exc: Exception) -> None:
    """Convert service-layer exceptions to appropriate HTTP responses."""
    rid = request_id_ctx.get("")
    if isinstance(exc, (ModelNotFoundError, ModelLoadError)):
        logger.error(
            "Model unavailable for '%s': %s  [request_id=%s]",
            disease_key, exc, rid
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ErrorDetail(
                error="model_unavailable",
                message=(
                    f"The prediction model for '{disease_key}' is not available. "
                    "Please ensure the models have been trained by running train_models.py."
                ),
                request_id=rid or None,
            ).model_dump(),
        )
    logger.exception(
        "Unexpected error during prediction for '%s'  [request_id=%s]",
        disease_key, rid
    )
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=ErrorDetail(
            error="prediction_failed",
            message="An unexpected error occurred during prediction. Please try again.",
            request_id=rid or None,
        ).model_dump(),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/breast-cancer",
    response_model=MedicalReport,
    status_code=status.HTTP_200_OK,
    summary="Breast Cancer Risk Assessment",
    description=(
        "Analyses cytological features from a Fine Needle Aspirate (FNA) biopsy "
        "and returns a comprehensive pathology-style medical report classifying "
        "the sample as Malignant or Benign with a full 10-section clinical analysis."
    ),
    responses={
        422: {"description": "Validation error — invalid or out-of-range input values."},
        503: {"description": "Model files not found — run train_models.py first."},
        500: {"description": "Internal server error during inference."},
    },
)
def predict_breast_cancer(data: BreastCancerRequest) -> MedicalReport:
    """
    Breast cancer risk prediction endpoint.

    Accepts 5 FNA cytological measurements and returns a MedicalReport
    with prediction, confidence, risk level, and full clinical analysis.
    """
    logger.info(
        "Received breast cancer prediction request: %s",
        data.model_dump()
    )
    try:
        return run_prediction("breast-cancer", data.to_feature_dict())
    except Exception as exc:
        _handle_prediction_error("breast-cancer", exc)


@router.post(
    "/diabetes",
    response_model=MedicalReport,
    status_code=status.HTTP_200_OK,
    summary="Type 2 Diabetes Risk Assessment",
    description=(
        "Analyses metabolic markers and demographic data to assess Type 2 Diabetes "
        "Mellitus risk, returning a comprehensive endocrinology-style report with "
        "glucose interpretation, personalised recommendations, and prevention guidance."
    ),
    responses={
        422: {"description": "Validation error — invalid or out-of-range input values."},
        503: {"description": "Model files not found — run train_models.py first."},
        500: {"description": "Internal server error during inference."},
    },
)
def predict_diabetes(data: DiabetesRequest) -> MedicalReport:
    """
    Type 2 Diabetes risk prediction endpoint.

    Accepts 5 metabolic/demographic indicators and returns a MedicalReport
    with prediction, confidence, risk level, and full clinical analysis.
    """
    logger.info(
        "Received diabetes prediction request: %s",
        data.model_dump()
    )
    try:
        return run_prediction("diabetes", data.to_feature_dict())
    except Exception as exc:
        _handle_prediction_error("diabetes", exc)


@router.post(
    "/heart-disease",
    response_model=MedicalReport,
    status_code=status.HTTP_200_OK,
    summary="Coronary Heart Disease Risk Assessment",
    description=(
        "Analyses cardiac indicators from the Cleveland Heart Disease dataset to "
        "assess coronary artery disease risk, returning a cardiology-style report "
        "with cholesterol interpretation, chest pain analysis, and cardiac guidance."
    ),
    responses={
        422: {"description": "Validation error — invalid or out-of-range input values."},
        503: {"description": "Model files not found — run train_models.py first."},
        500: {"description": "Internal server error during inference."},
    },
)
def predict_heart_disease(data: HeartDiseaseRequest) -> MedicalReport:
    """
    Coronary heart disease risk prediction endpoint.

    Accepts 5 cardiac indicators and returns a MedicalReport with prediction,
    confidence, risk level, and full clinical cardiology analysis.
    """
    logger.info(
        "Received heart disease prediction request: %s",
        data.model_dump()
    )
    try:
        return run_prediction("heart-disease", data.to_feature_dict())
    except Exception as exc:
        _handle_prediction_error("heart-disease", exc)
