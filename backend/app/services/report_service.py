"""
Medical Report Service.

Contains one ReportGenerator subclass per disease. Each generator
produces all 10 structured sections of the MedicalReport response.

Architecture:
  - BaseReportGenerator defines the interface and shared helpers.
  - Disease-specific subclasses override `generate()`.
  - REPORT_REGISTRY maps disease slugs → generator instances.

Adding a new disease:
  1. Create a new subclass of BaseReportGenerator.
  2. Register it in REPORT_REGISTRY at the bottom of this file.
  No other files need modification.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

from app.schemas.responses import (
    ContributingFactor,
    LifestyleRecommendations,
    MedicalReport,
)
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

RiskLevel = Literal["Low", "Moderate", "High"]

_DISCLAIMER = (
    "⚠️ This AI-generated report is intended for educational and screening "
    "purposes only. It is NOT a substitute for professional medical advice, "
    "diagnosis, or treatment. The predictions reflect statistical risk patterns "
    "and cannot definitively confirm or rule out any medical condition. "
    "Always consult a qualified and licensed healthcare professional before "
    "making any medical decisions. In the case of a medical emergency, "
    "contact emergency services immediately."
)


# ─────────────────────────────────────────────────────────────────────────────
# Base Class
# ─────────────────────────────────────────────────────────────────────────────

class BaseReportGenerator(ABC):
    """Abstract base for all disease-specific report generators."""

    disease_name: str = ""
    specialist_role: str = ""

    # ── Abstract interface ──────────────────────────────────────────────────

    @abstractmethod
    def generate(
        self,
        inputs: dict[str, float],
        prediction_label: str,
        confidence: float,
        risk_level: RiskLevel,
    ) -> MedicalReport:
        """Build and return a complete MedicalReport."""

    # ── Shared helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _format_confidence(confidence: float) -> str:
        return f"{confidence * 100:.1f}%"

    @staticmethod
    def _factor(
        name: str,
        value: float,
        unit: str,
        normal_range: str,
        status: Literal["Normal", "Borderline", "Abnormal"],
        interpretation: str,
    ) -> ContributingFactor:
        return ContributingFactor(
            name=name,
            value=f"{value} {unit}".strip(),
            normal_range=normal_range,
            status=status,
            interpretation=interpretation,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Breast Cancer Generator
# ─────────────────────────────────────────────────────────────────────────────

class BreastCancerReportGenerator(BaseReportGenerator):
    disease_name = "Breast Cancer"
    specialist_role = "Lead Pathologist / Oncologist"

    def generate(
        self,
        inputs: dict[str, float],
        prediction_label: str,
        confidence: float,
        risk_level: RiskLevel,
    ) -> MedicalReport:
        is_malignant = prediction_label == "Malignant"
        conf_str = self._format_confidence(confidence)

        radius = inputs.get("mean radius", 0)
        texture = inputs.get("mean texture", 0)
        perimeter = inputs.get("mean perimeter", 0)
        area = inputs.get("mean area", 0)
        smoothness = inputs.get("mean smoothness", 0)

        # ── Section 1 — Prediction Summary ─────────────────────────────────
        if is_malignant:
            prediction_summary = (
                f"Based on the cytological features extracted from your Fine Needle "
                f"Aspirate (FNA) biopsy, our predictive model indicates a "
                f"'{prediction_label}' profile with a confidence of {conf_str}. "
                f"This represents a {risk_level.lower()} risk assessment and warrants "
                f"prompt clinical evaluation by a qualified oncologist or breast "
                f"specialist to confirm these findings with formal diagnostic imaging "
                f"and tissue examination."
            )
        else:
            prediction_summary = (
                f"Based on the cytological features extracted from your Fine Needle "
                f"Aspirate (FNA) biopsy, our predictive model indicates a "
                f"'{prediction_label}' (non-cancerous) cellular profile with a "
                f"confidence of {conf_str}. The cell morphology appears to reflect "
                f"normal, healthy tissue growth patterns. This is a reassuring "
                f"assessment, though routine clinical follow-up remains important."
            )

        # ── Section 2 — Explanation ─────────────────────────────────────────
        if is_malignant:
            explanation = (
                f"The AI model analysed five key morphological features of your "
                f"biopsy cell nuclei. Malignant (cancerous) cells typically exhibit "
                f"larger, more irregular, and more rapidly dividing nuclei compared "
                f"to benign cells. Your cellular profile — particularly the combination "
                f"of radius ({radius:.2f} mm), area ({area:.1f} mm²), and texture "
                f"variation ({texture:.2f}) — aligns more closely with patterns "
                f"observed in malignant tissue in the training dataset of 569 labelled "
                f"biopsy samples. The model does not replace a biopsy confirmation but "
                f"serves as a powerful early screening tool."
            )
        else:
            explanation = (
                f"The AI model analysed five key morphological features of your "
                f"biopsy cell nuclei. Your values — radius ({radius:.2f} mm), "
                f"texture ({texture:.2f}), perimeter ({perimeter:.2f} mm), "
                f"area ({area:.1f} mm²), and smoothness ({smoothness:.4f}) — "
                f"collectively match the profile of benign cellular formations more "
                f"closely than malignant ones. Benign cells tend to have smaller, "
                f"more uniform nuclei with regular boundaries. Your profile is "
                f"consistent with these healthy characteristics."
            )

        # ── Section 3 — Clinical Interpretation ────────────────────────────
        factors: list[ContributingFactor] = []

        radius_status: Literal["Normal", "Borderline", "Abnormal"] = (
            "Abnormal" if radius > 17 else "Borderline" if radius > 14 else "Normal"
        )
        factors.append(self._factor(
            "Mean Nuclear Radius", radius, "mm", "< 14.0 mm",
            radius_status,
            (
                "The mean radius reflects the average size of the cell nuclei. "
                + (
                    f"A radius of {radius:.2f} mm is elevated, indicating enlarged nuclei "
                    "which is a hallmark of abnormal, potentially malignant cell growth."
                    if radius > 14
                    else f"A radius of {radius:.2f} mm falls within a normal range, "
                    "suggesting regular cell size consistent with benign tissue."
                )
            )
        ))

        texture_status: Literal["Normal", "Borderline", "Abnormal"] = (
            "Abnormal" if texture > 22 else "Borderline" if texture > 18 else "Normal"
        )
        factors.append(self._factor(
            "Mean Nuclear Texture", texture, "(SD grey-scale)", "< 18.0",
            texture_status,
            (
                f"Nuclear texture ({texture:.2f}) measures the standard deviation of "
                "grey-scale values in the nucleus image. "
                + (
                    "Higher texture variance indicates a non-uniform, irregular surface "
                    "pattern — a common feature of malignant nuclei."
                    if texture > 18
                    else "Low texture variance indicates uniform nuclear composition, "
                    "consistent with well-differentiated, benign tissue."
                )
            )
        ))

        area_status: Literal["Normal", "Borderline", "Abnormal"] = (
            "Abnormal" if area > 800 else "Borderline" if area > 600 else "Normal"
        )
        factors.append(self._factor(
            "Mean Nuclear Area", area, "mm²", "< 600 mm²",
            area_status,
            (
                f"Nuclear area ({area:.1f} mm²) directly reflects the size of the cell nucleus. "
                + (
                    "An area above 600 mm² is considered enlarged and is strongly associated "
                    "with active, potentially invasive cell division."
                    if area > 600
                    else "An area below 600 mm² is consistent with normal cell dimensions."
                )
            )
        ))

        smoothness_status: Literal["Normal", "Borderline", "Abnormal"] = (
            "Abnormal" if smoothness > 0.13 else "Borderline" if smoothness > 0.10 else "Normal"
        )
        factors.append(self._factor(
            "Mean Smoothness", smoothness, "", "0.05 – 0.10",
            smoothness_status,
            (
                f"Smoothness ({smoothness:.4f}) measures local variation in radius lengths. "
                + (
                    "Higher smoothness values indicate irregular nuclear borders, "
                    "which are characteristic of malignant cells that grow without "
                    "the structural constraints of normal tissue."
                    if smoothness > 0.10
                    else "Low smoothness values indicate regular, well-defined nuclear "
                    "borders consistent with benign tissue architecture."
                )
            )
        ))

        if is_malignant:
            clinical_interpretation = (
                f"As your reviewing pathologist, I have carefully examined the five "
                f"cytological parameters from your FNA report. Several of your "
                f"indicators — particularly the nuclear radius ({radius:.2f} mm), "
                f"area ({area:.1f} mm²), and texture ({texture:.2f}) — fall outside "
                f"or near the boundary of what we typically observe in benign tissue. "
                f"Malignant cells characteristically show nuclear pleomorphism (variation "
                f"in size and shape), hyperchromasia (darker staining), and loss of "
                f"cohesion. The pattern in your data is consistent with these features "
                f"and merits urgent formal histopathological evaluation. I want to "
                f"emphasise that this is a screening tool — a confirmed diagnosis "
                f"requires a core-needle biopsy reviewed by a certified pathologist."
            )
        else:
            clinical_interpretation = (
                f"Reviewing your cytological parameters, I am reassured by the overall "
                f"profile. Your nuclear radius ({radius:.2f} mm), area ({area:.1f} mm²), "
                f"and texture ({texture:.2f}) are largely within or near normal ranges. "
                f"Benign cells tend to maintain their nuclear structure and grow in an "
                f"orderly fashion. The features presented are consistent with normal "
                f"ductal or lobular breast tissue. Continued routine surveillance "
                f"remains the recommended course of action."
            )

        # ── Section 4 — Lifestyle Recommendations ──────────────────────────
        lifestyle = LifestyleRecommendations(
            diet=[
                "Prioritise a diet rich in cruciferous vegetables (broccoli, kale, cauliflower) — they contain sulforaphane, shown to have anti-cancer properties.",
                "Include antioxidant-rich foods: blueberries, tomatoes, green tea, and turmeric.",
                "Reduce consumption of processed meats, red meats, and ultra-processed snacks.",
                "Limit dietary fat, particularly saturated fats from red meat and full-fat dairy.",
                "Choose fibre-rich whole grains, legumes, and fruits to support hormonal balance.",
            ],
            physical_activity=[
                "Aim for at least 150 minutes of moderate aerobic exercise per week (e.g., brisk walking, cycling, swimming).",
                "Include 2 sessions of strength training per week — muscle mass supports metabolic health.",
                "Regular physical activity is associated with significantly reduced breast cancer recurrence and risk.",
            ],
            sleep=[
                "Aim for 7–9 hours of uninterrupted sleep per night.",
                "Disrupted circadian rhythm (shift work, late nights) is linked to increased breast cancer risk — maintain consistent sleep schedules.",
                "Create a dark, cool, and electronics-free sleep environment.",
            ],
            weight_management=[
                "Maintain a healthy BMI (18.5–24.9). Excess body fat, especially post-menopause, elevates oestrogen levels and breast cancer risk.",
                "Avoid crash diets — sustainable, gradual weight loss is safer and more effective.",
            ],
            hydration=[
                "Drink 8–10 glasses (2–2.5 litres) of water daily.",
                "Limit sugary beverages and artificially sweetened drinks.",
            ],
            stress_management=[
                "Chronic stress suppresses immune surveillance. Practise daily mindfulness, meditation, or yoga.",
                "Seek counselling or support groups if you are experiencing health-related anxiety.",
                "Social connection and psychological support are important components of holistic cancer care.",
            ],
            smoking=[
                "Smoking is a significant carcinogen. If you smoke, consult your doctor about cessation programmes immediately.",
                "Avoid secondhand smoke exposure.",
            ],
            alcohol=[
                "Alcohol is a Group 1 carcinogen with a proven dose-dependent link to breast cancer.",
                "Limit intake to a maximum of 1 unit per day, or ideally eliminate alcohol entirely.",
            ],
        )

        # ── Section 5 — Do's ────────────────────────────────────────────────
        if is_malignant:
            dos = [
                "Schedule an urgent appointment with a board-certified oncologist or breast surgeon.",
                "Request a diagnostic mammogram, breast ultrasound, or MRI to complement the FNA findings.",
                "Ask for a core-needle biopsy for definitive histopathological classification.",
                "Bring a trusted family member or advocate to all medical appointments for support.",
                "Maintain a detailed symptom and medication diary.",
                "Seek a second pathological opinion if you have any doubts.",
                "Ask your doctor about genetic testing (BRCA1/BRCA2) if you have a family history.",
                "Engage with a breast cancer nurse specialist or patient navigator.",
            ]
        else:
            dos = [
                "Continue routine annual mammograms as per your age and risk guidelines.",
                "Perform monthly breast self-examinations — report any new lumps, skin changes, or nipple discharge promptly.",
                "Attend all scheduled clinical breast exams with your healthcare provider.",
                "Maintain a healthy body weight and active lifestyle.",
                "Follow up with your doctor for any persistent breast-related concerns.",
                "Discuss your family history with your GP to assess if enhanced surveillance is warranted.",
            ]

        # ── Section 6 — Don'ts ──────────────────────────────────────────────
        if is_malignant:
            donts = [
                "Do not delay seeking specialist evaluation — early intervention significantly improves outcomes.",
                "Do not self-diagnose or rely solely on this AI screening tool.",
                "Do not ignore pain, swelling, skin dimpling, nipple changes, or discharge.",
                "Do not start or stop any medication without medical supervision.",
                "Do not share your results on social media before getting a formal diagnosis — seek professional clarity first.",
                "Do not consume excessive alcohol or continue smoking during this period.",
            ]
        else:
            donts = [
                "Do not skip regular mammogram screenings, even with a reassuring result today.",
                "Do not ignore new or changing breast symptoms — always have them evaluated.",
                "Do not assume this result eliminates all cancer risk — annual screening remains essential.",
                "Do not consume alcohol excessively or smoke — these elevate breast cancer risk over time.",
            ]

        # ── Section 7 — When to See a Doctor ───────────────────────────────
        if is_malignant:
            when_to_see_doctor = (
                "URGENT: Please contact a breast oncologist or surgeon within the next "
                "few days. This screening result warrants priority clinical review. "
                "Seek emergency medical attention IMMEDIATELY if you experience: "
                "rapid swelling, severe breast pain, skin ulceration, or axillary "
                "(armpit) lymph node swelling. Follow-up tests to request: "
                "diagnostic mammogram, breast MRI, core-needle biopsy, lymph node "
                "ultrasound, and a full blood panel."
            )
        else:
            when_to_see_doctor = (
                "Schedule your next routine breast examination with your GP or gynaecologist "
                "as per national screening guidelines (typically annually after age 40, "
                "or as advised). Seek prompt medical attention if you notice: new lumps, "
                "skin changes (dimpling, redness, peau d'orange texture), nipple retraction "
                "or discharge, unexplained breast pain, or axillary lumps."
            )

        # ── Section 8 — Preventive Care ────────────────────────────────────
        preventive_care = [
            "Annual clinical breast examination by a qualified healthcare provider.",
            "Mammography screening as per national guidelines (typically every 1–2 years for women 40+).",
            "Breast self-awareness: learn the normal look and feel of your breasts.",
            "Genetic counselling if you have a first-degree relative with breast or ovarian cancer.",
            "BRCA1/BRCA2 genetic testing if family history warrants it.",
            "Maintain a healthy weight, active lifestyle, and low alcohol consumption.",
            "Discuss hormone replacement therapy (HRT) risks with your doctor if applicable.",
            "Consider annual check-ups with blood tests to monitor general health markers.",
        ]

        # ── Section 9 — In Simple Words ────────────────────────────────────
        if is_malignant:
            in_simple_words = (
                f"In simple terms, the computer has looked at the measurements from your "
                f"breast cell sample and found some patterns that look similar to what we "
                f"see in cancer cells — specifically, the cells appear to be larger and "
                f"more irregular than normal. The computer is about {conf_str} confident "
                f"in this finding. This does NOT mean you definitely have cancer. It means "
                f"the results are concerning enough that a real doctor needs to examine you "
                f"and run more tests (like a proper biopsy) to know for sure. Think of this "
                f"like a smoke alarm going off — it might be a fire, or it might be burnt "
                f"toast, but you should definitely check. Please see a doctor soon."
            )
        else:
            in_simple_words = (
                f"In simple terms, the computer looked at the measurements from your breast "
                f"cell sample and found patterns that look similar to healthy, non-cancerous "
                f"cells — the cells appear to be the right size and shape. The computer is "
                f"about {conf_str} confident in this reassuring finding. This does NOT mean "
                f"you are 100% free of any health concerns forever — it just means right now, "
                f"based on these measurements, things look normal. Keep going for your regular "
                f"check-ups and don't hesitate to see your doctor if anything changes."
            )

        return MedicalReport(
            disease_name=self.disease_name,
            specialist_role=self.specialist_role,
            prediction_label=prediction_label,
            confidence_score=round(confidence, 4),
            risk_level=risk_level,
            prediction_summary=prediction_summary,
            explanation=explanation,
            clinical_interpretation=clinical_interpretation,
            contributing_factors=factors,
            lifestyle_recommendations=lifestyle,
            dos=dos,
            donts=donts,
            when_to_see_doctor=when_to_see_doctor,
            preventive_care=preventive_care,
            in_simple_words=in_simple_words,
            disclaimer=_DISCLAIMER,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Diabetes Generator
# ─────────────────────────────────────────────────────────────────────────────

class DiabetesReportGenerator(BaseReportGenerator):
    disease_name = "Type 2 Diabetes Mellitus"
    specialist_role = "Lead Endocrinologist / Diabetologist"

    def generate(
        self,
        inputs: dict[str, float],
        prediction_label: str,
        confidence: float,
        risk_level: RiskLevel,
    ) -> MedicalReport:
        is_positive = prediction_label == "Positive"
        conf_str = self._format_confidence(confidence)

        pregnancies = inputs.get("Pregnancies", 0)
        glucose = inputs.get("Glucose", 0)
        bp = inputs.get("BloodPressure", 0)
        bmi = inputs.get("BMI", 0)
        age = inputs.get("Age", 0)

        # ── Section 1 — Prediction Summary ─────────────────────────────────
        if is_positive:
            prediction_summary = (
                f"Based on your metabolic markers and demographic profile, our "
                f"predictive model indicates a {risk_level.lower()} risk "
                f"({conf_str} confidence) of Type 2 Diabetes Mellitus (T2DM). "
                f"Your glucose levels, BMI, and blood pressure collectively suggest "
                f"a metabolic profile consistent with insulin resistance and impaired "
                f"glucose regulation. Formal clinical evaluation with an HbA1c test "
                f"and fasting lipid panel is strongly advised."
            )
        else:
            prediction_summary = (
                f"Based on your metabolic markers, our predictive model indicates a "
                f"low risk ({conf_str} confidence) of Type 2 Diabetes Mellitus at "
                f"this time. Your glucose level, BMI, and blood pressure are "
                f"collectively within or near healthy ranges. Maintaining your "
                f"current lifestyle and continuing routine metabolic monitoring "
                f"remains the recommended course of action."
            )

        # ── Section 2 — Explanation ─────────────────────────────────────────
        if is_positive:
            explanation = (
                f"The model evaluated five key metabolic and demographic indicators: "
                f"fasting glucose ({glucose} mg/dL), BMI ({bmi}), diastolic blood "
                f"pressure ({bp} mmHg), number of pregnancies ({int(pregnancies)}), "
                f"and age ({int(age)} years). Elevated glucose is the most direct "
                f"indicator of diabetes. Combined with a BMI of {bmi} and the "
                f"presence of hypertension, your overall profile matches patterns "
                f"associated with metabolic syndrome — a precursor and co-condition "
                f"of Type 2 Diabetes. The model learned these patterns from the "
                f"Pima Indians Diabetes Dataset (768 patients) and is calibrated "
                f"for early-stage detection."
            )
        else:
            explanation = (
                f"The model evaluated your fasting glucose ({glucose} mg/dL), "
                f"BMI ({bmi}), diastolic blood pressure ({bp} mmHg), pregnancies "
                f"({int(pregnancies)}), and age ({int(age)} years). Your values "
                f"collectively align more closely with the non-diabetic population "
                f"in the model's training dataset. Glucose is the primary driver — "
                f"at {glucose} mg/dL, it falls in a range that does not strongly "
                f"signal insulin resistance or impaired glucose tolerance."
            )

        # ── Section 3 — Clinical Interpretation ────────────────────────────
        factors: list[ContributingFactor] = []

        glucose_status: Literal["Normal", "Borderline", "Abnormal"] = (
            "Abnormal" if glucose >= 126 else "Borderline" if glucose >= 100 else "Normal"
        )
        factors.append(self._factor(
            "Fasting Plasma Glucose", glucose, "mg/dL",
            "< 100 mg/dL (normal), 100–125 (pre-diabetic), ≥ 126 (diabetic)",
            glucose_status,
            (
                f"Your glucose level of {glucose} mg/dL is "
                + (
                    "significantly above the diabetic threshold of 126 mg/dL, meeting "
                    "a primary diagnostic criterion for T2DM. Insulin is failing to "
                    "adequately clear glucose from the bloodstream."
                    if glucose >= 126
                    else "in the pre-diabetic range (100–125 mg/dL), indicating impaired "
                    "fasting glucose and early insulin resistance. Lifestyle intervention "
                    "now can prevent progression to diabetes."
                    if glucose >= 100
                    else "within the normal fasting range, indicating healthy glucose "
                    "metabolism and adequate insulin sensitivity."
                )
            )
        ))

        bmi_status: Literal["Normal", "Borderline", "Abnormal"] = (
            "Abnormal" if bmi >= 30 else "Borderline" if bmi >= 25 else "Normal"
        )
        factors.append(self._factor(
            "Body Mass Index (BMI)", bmi, "kg/m²",
            "18.5–24.9 (normal weight)",
            bmi_status,
            (
                f"BMI of {bmi} falls in the "
                + (
                    f"obese range (≥ 30). Obesity dramatically increases insulin "
                    f"resistance — adipose tissue secretes inflammatory cytokines "
                    f"that interfere with insulin receptor signalling."
                    if bmi >= 30
                    else f"overweight range (25–29.9). Excess body fat, particularly "
                    f"abdominal/visceral fat, contributes to metabolic dysfunction."
                    if bmi >= 25
                    else f"healthy range. A normal BMI significantly reduces metabolic "
                    f"disease risk."
                )
            )
        ))

        bp_status: Literal["Normal", "Borderline", "Abnormal"] = (
            "Abnormal" if bp >= 90 else "Borderline" if bp >= 80 else "Normal"
        )
        factors.append(self._factor(
            "Diastolic Blood Pressure", bp, "mmHg",
            "< 80 mmHg (normal diastolic)",
            bp_status,
            (
                f"Diastolic pressure of {bp} mmHg is "
                + (
                    "elevated (≥ 90 mmHg = Stage 2 hypertension). Hypertension "
                    "frequently co-occurs with diabetes as part of metabolic syndrome "
                    "and increases the risk of cardiovascular complications."
                    if bp >= 90
                    else "mildly elevated (80–89 mmHg = Stage 1 hypertension). "
                    "This warrants monitoring alongside other metabolic risk factors."
                    if bp >= 80
                    else "within normal range, which is a positive metabolic indicator."
                )
            )
        ))

        age_status: Literal["Normal", "Borderline", "Abnormal"] = (
            "Abnormal" if age >= 65 else "Borderline" if age >= 45 else "Normal"
        )
        factors.append(self._factor(
            "Age", age, "years",
            "Risk increases after age 45",
            age_status,
            (
                f"At age {int(age)}, "
                + (
                    "you are in the highest age-related risk category for T2DM. "
                    "Insulin secretion and sensitivity naturally decline with age, "
                    "making metabolic management increasingly important."
                    if age >= 65
                    else "you are entering a higher-risk decade (45–64) where diabetes "
                    "prevalence increases significantly. Proactive monitoring is advisable."
                    if age >= 45
                    else "your age group has relatively lower age-related diabetes risk. "
                    "However, other metabolic factors remain important."
                )
            )
        ))

        if is_positive:
            clinical_interpretation = (
                f"As your endocrinologist, I am reviewing your metabolic panel with "
                f"concern. Your fasting glucose of {glucose} mg/dL "
                f"{'exceeds' if glucose >= 126 else 'approaches'} the diagnostic "
                f"threshold for Type 2 Diabetes. Combined with your BMI of {bmi} "
                f"({'obese' if bmi >= 30 else 'overweight' if bmi >= 25 else 'normal'}) "
                f"and a diastolic blood pressure of {bp} mmHg, your profile is "
                f"consistent with metabolic syndrome — a cluster of conditions that "
                f"dramatically elevate your risk of T2DM, cardiovascular disease, and "
                f"non-alcoholic fatty liver disease. I want to be clear: this model "
                f"is a screening instrument. An HbA1c test, which measures your "
                f"average blood sugar over the past 3 months, is the gold standard "
                f"for diagnosis. Please do not self-treat."
            )
        else:
            clinical_interpretation = (
                f"Reviewing your metabolic panel, I am reassured by the overall "
                f"picture. Your fasting glucose of {glucose} mg/dL is "
                f"{'at the lower end of normal' if glucose < 90 else 'within an acceptable range'}. "
                f"Your BMI of {bmi} and blood pressure of {bp} mmHg are both "
                f"manageable. At age {int(age)}, maintaining these values through "
                f"diet and exercise remains the most effective preventive strategy. "
                f"There is no single safe result — metabolic health is dynamic and "
                f"must be monitored annually."
            )

        # ── Section 4 — Lifestyle Recommendations ──────────────────────────
        lifestyle = LifestyleRecommendations(
            diet=[
                "Follow a low-glycaemic index (GI) diet: choose brown rice, wholegrain bread, lentils, and chickpeas over white rice and refined carbs.",
                "Increase non-starchy vegetables: spinach, broccoli, capsicum, cucumber — aim for half your plate.",
                "Include healthy fats: avocado, nuts, olive oil, fatty fish (salmon, sardines) to improve insulin sensitivity.",
                "Reduce added sugars: eliminate sugary drinks (soda, fruit juices, energy drinks), desserts, and confectionery.",
                "Eat 3 structured meals per day with 2 healthy snacks — avoid prolonged fasting followed by large meals.",
                "Prioritise protein at each meal to slow glucose absorption: eggs, legumes, lean poultry, tofu.",
            ] + (
                [f"Specifically for your glucose of {glucose} mg/dL: portion-control carbohydrate intake and consider speaking with a dietitian about a structured meal plan."]
                if glucose >= 100 else []
            ),
            physical_activity=[
                "Engage in at least 150 minutes of moderate aerobic exercise per week (brisk walking, cycling, swimming).",
                "Include 2–3 sessions of resistance training weekly — muscle mass improves glucose uptake without insulin.",
                "Reduce sedentary time: aim to stand or walk for at least 5 minutes every hour.",
                "Post-meal walks (even 10–15 minutes) are highly effective at blunting blood sugar spikes.",
            ],
            sleep=[
                "Sleep deprivation raises cortisol and ghrelin — hormones that increase blood sugar and hunger. Aim for 7–9 hours.",
                "Treat obstructive sleep apnoea if present — it significantly worsens insulin resistance.",
                "Avoid screens 1 hour before bed and maintain a consistent sleep-wake schedule.",
            ],
            weight_management=[
                f"{'A weight loss of 5–10% of your body weight can reduce diabetes risk by up to 58%. This is your most impactful intervention.' if bmi >= 25 else 'Maintain your healthy weight through balanced nutrition and regular physical activity.'}",
                "Set gradual, realistic goals: 0.5–1 kg loss per week is sustainable and evidence-based.",
                "Consult a registered dietitian for a personalised, medically supervised weight management plan.",
            ],
            hydration=[
                "Drink 8–10 glasses (2–2.5 litres) of water daily — dehydration concentrates blood glucose.",
                "Replace all sugary beverages with water, herbal teas, or sparkling water.",
                "Limit caffeine to 1–2 cups daily — excess caffeine can affect blood sugar levels.",
            ],
            stress_management=[
                "Chronic stress elevates cortisol, which raises blood glucose. Daily stress reduction is medically important.",
                "Practise mindfulness, meditation, deep breathing (4-7-8 technique), or yoga for 15–20 minutes daily.",
                "Identify and address stressors with a therapist or counsellor if needed.",
            ],
            smoking=[
                "Smoking increases insulin resistance by up to 40%. Cessation is a high-priority medical recommendation.",
                "Seek smoking cessation support via your GP, nicotine replacement therapy, or prescription medication.",
            ],
            alcohol=[
                "Alcohol disrupts glucose regulation. Limit to 1 unit/day (women) or 2 units/day (men), or eliminate entirely.",
                "Never drink alcohol on an empty stomach — it can cause dangerous hypoglycaemia, especially with diabetes medication.",
            ],
        )

        # ── Section 5 — Do's ────────────────────────────────────────────────
        if is_positive:
            dos = [
                "Book an appointment with your GP or endocrinologist within the next 2 weeks for an HbA1c test.",
                "Request a fasting lipid panel, kidney function tests (eGFR, creatinine), and liver function tests.",
                "Monitor your blood pressure regularly — home monitoring kits are widely available and recommended.",
                "Begin a structured dietary overhaul: eliminate refined carbohydrates and added sugars immediately.",
                "Start a daily 30-minute walking routine if not already exercising.",
                "Keep a food and glucose diary to track patterns.",
                "Join a diabetes prevention programme (DPP) — these are evidence-based and highly effective.",
                "Inform your family members of your risk — Type 2 Diabetes has strong hereditary components.",
            ]
        else:
            dos = [
                "Continue your healthy lifestyle — it is your strongest protective factor.",
                "Have your fasting glucose and HbA1c tested annually.",
                "Monitor your BMI and waist circumference regularly.",
                "Engage in regular aerobic and resistance exercise.",
                "Follow a balanced, low-GI diet rich in vegetables, whole grains, and lean protein.",
                "Stay well hydrated and avoid sugary beverages.",
            ]

        # ── Section 6 — Don'ts ──────────────────────────────────────────────
        if is_positive:
            donts = [
                "Do not delay clinical evaluation — early intervention prevents irreversible complications.",
                "Do not self-medicate with supplements, herbal remedies, or unverified online treatments.",
                "Do not consume sugary foods, refined carbohydrates, or sugary drinks.",
                "Do not skip meals — irregular eating patterns destabilise blood glucose levels.",
                "Do not attempt extreme fasting or crash dieting without medical supervision.",
                "Do not ignore symptoms such as excessive thirst, frequent urination, blurred vision, or fatigue.",
                "Do not smoke — it significantly worsens insulin resistance.",
            ]
        else:
            donts = [
                "Do not neglect annual metabolic screening — diabetes can develop silently.",
                "Do not overindulge in sugary foods, refined carbohydrates, or alcohol.",
                "Do not ignore weight gain, increased thirst, or unusual fatigue.",
                "Do not lead a sedentary lifestyle — physical inactivity is a primary diabetes risk factor.",
            ]

        # ── Section 7 — When to See a Doctor ───────────────────────────────
        if is_positive:
            when_to_see_doctor = (
                "Please seek medical consultation within the next 1–2 weeks. "
                "Key tests to request: HbA1c (gold-standard diabetes test), fasting "
                "plasma glucose, fasting lipid panel, kidney function (eGFR, creatinine, "
                "urea), urine microalbumin, liver function tests, and thyroid function. "
                "Seek EMERGENCY care if you experience: extreme thirst and urination, "
                "severe fatigue, blurred vision, confusion, sweet-smelling breath, "
                "or loss of consciousness — these may indicate diabetic ketoacidosis (DKA)."
            )
        else:
            when_to_see_doctor = (
                "Schedule a routine check-up annually with your GP. "
                "Request fasting glucose and HbA1c annually if you are over 35, "
                "have a family history of diabetes, or are overweight. "
                "See your doctor promptly if you develop: excessive thirst, "
                "frequent urination, unexplained weight loss, persistent fatigue, "
                "slow wound healing, or tingling in hands/feet."
            )

        # ── Section 8 — Preventive Care ────────────────────────────────────
        preventive_care = [
            "Annual fasting glucose and HbA1c testing.",
            "Annual blood pressure monitoring.",
            "Lipid panel (cholesterol test) every 1–2 years.",
            "Maintain a BMI within the healthy range (18.5–24.9).",
            "Participate in a structured Diabetes Prevention Programme if at elevated risk.",
            "Eye examination annually (diabetic retinopathy screening if diagnosed).",
            "Foot examination annually to check for neuropathy.",
            "Dental check-ups every 6 months — gum disease is linked to poor glucose control.",
            "Kidney function tests annually if at risk.",
        ]

        # ── Section 9 — In Simple Words ────────────────────────────────────
        if is_positive:
            in_simple_words = (
                f"In simple terms: the computer looked at your blood sugar level "
                f"({glucose} mg/dL), your weight (BMI {bmi}), your blood pressure "
                f"({bp} mmHg), and your age ({int(age)}), and found that these "
                f"numbers look similar to people who have or are at high risk of "
                f"developing diabetes. Think of diabetes like this: your body normally "
                f"uses a hormone called insulin like a key to unlock your cells and let "
                f"sugar in for energy. In diabetes, the key stops working properly, so "
                f"sugar builds up in your blood instead. The computer is {conf_str} "
                f"confident in this assessment. This does NOT mean you definitely have "
                f"diabetes — but it strongly suggests you should see a doctor for a "
                f"proper blood test. The good news is that with the right lifestyle "
                f"changes, diabetes can often be prevented or significantly delayed."
            )
        else:
            in_simple_words = (
                f"In simple terms: the computer looked at your blood sugar "
                f"({glucose} mg/dL), weight (BMI {bmi}), blood pressure ({bp} mmHg), "
                f"and age ({int(age)}), and found that your numbers look more like "
                f"someone without diabetes — which is a good sign! Think of your body "
                f"like a well-tuned engine right now. Keep it running well by eating "
                f"healthy foods, exercising regularly, and getting annual blood tests. "
                f"The computer is {conf_str} confident in this reassuring finding."
            )

        return MedicalReport(
            disease_name=self.disease_name,
            specialist_role=self.specialist_role,
            prediction_label=prediction_label,
            confidence_score=round(confidence, 4),
            risk_level=risk_level,
            prediction_summary=prediction_summary,
            explanation=explanation,
            clinical_interpretation=clinical_interpretation,
            contributing_factors=factors,
            lifestyle_recommendations=lifestyle,
            dos=dos,
            donts=donts,
            when_to_see_doctor=when_to_see_doctor,
            preventive_care=preventive_care,
            in_simple_words=in_simple_words,
            disclaimer=_DISCLAIMER,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Heart Disease Generator
# ─────────────────────────────────────────────────────────────────────────────

class HeartDiseaseReportGenerator(BaseReportGenerator):
    disease_name = "Coronary Heart Disease"
    specialist_role = "Lead Cardiologist / Cardiovascular Specialist"

    _CP_LABELS = {
        1: "Typical Angina",
        2: "Atypical Angina",
        3: "Non-Anginal Pain",
        4: "Asymptomatic",
    }

    def generate(
        self,
        inputs: dict[str, float],
        prediction_label: str,
        confidence: float,
        risk_level: RiskLevel,
    ) -> MedicalReport:
        is_positive = prediction_label == "Presence"
        conf_str = self._format_confidence(confidence)

        age = inputs.get("age", 0)
        sex = inputs.get("sex", 0)
        cp = int(inputs.get("cp", 4))
        trestbps = inputs.get("trestbps", 0)
        chol = inputs.get("chol", 0)

        sex_label = "Male" if sex == 1 else "Female"
        cp_label = self._CP_LABELS.get(cp, "Unknown")

        # ── Section 1 — Prediction Summary ─────────────────────────────────
        if is_positive:
            prediction_summary = (
                f"Based on your cardiac indicators, our predictive model identifies a "
                f"{risk_level.lower()} risk ({conf_str} confidence) of coronary heart "
                f"disease (CHD) or a related cardiovascular condition. Your chest pain "
                f"pattern ({cp_label}), resting blood pressure ({trestbps} mmHg), and "
                f"serum cholesterol ({chol} mg/dL) — considered alongside your age "
                f"({int(age)}) and sex ({sex_label}) — present a cardiovascular risk "
                f"profile that warrants urgent specialist evaluation."
            )
        else:
            prediction_summary = (
                f"Based on your cardiac indicators, our predictive model identifies a "
                f"low risk ({conf_str} confidence) of coronary heart disease at this "
                f"time. Your cardiovascular profile — blood pressure ({trestbps} mmHg), "
                f"cholesterol ({chol} mg/dL), and chest pain type ({cp_label}) — "
                f"collectively suggests an absence of significant coronary artery "
                f"disease based on the evaluated parameters."
            )

        # ── Section 2 — Explanation ─────────────────────────────────────────
        if is_positive:
            explanation = (
                f"The model assessed five cardiac parameters from the Cleveland Heart "
                f"Disease Dataset. The most significant drivers in your case are: your "
                f"chest pain type ({cp_label}), which is clinically associated with "
                f"myocardial ischaemia; your resting blood pressure ({trestbps} mmHg), "
                f"which "
                + ("is above the hypertension threshold (≥ 140 mmHg) and places chronic "
                   "pressure on the arterial walls and heart muscle; "
                   if trestbps >= 140
                   else "is within range but contributes to the overall risk calculation; ")
                + f"and your cholesterol ({chol} mg/dL), "
                + ("which is elevated and accelerates atherosclerotic plaque formation in "
                   "the coronary arteries."
                   if chol >= 240
                   else "which is being factored alongside other cardiac indicators.")
                + f" Being a {sex_label} aged {int(age)} also modifies your baseline risk."
            )
        else:
            explanation = (
                f"The model assessed your five cardiac parameters: chest pain type "
                f"({cp_label}), resting blood pressure ({trestbps} mmHg), serum "
                f"cholesterol ({chol} mg/dL), age ({int(age)}), and sex ({sex_label}). "
                f"Collectively, these values align more closely with the low-risk "
                f"cardiovascular population in the training dataset. Your cholesterol "
                f"and blood pressure values are within a manageable range, and no "
                f"severe angina pattern was identified."
            )

        # ── Section 3 — Clinical Interpretation ────────────────────────────
        factors: list[ContributingFactor] = []

        chol_status: Literal["Normal", "Borderline", "Abnormal"] = (
            "Abnormal" if chol >= 240 else "Borderline" if chol >= 200 else "Normal"
        )
        factors.append(self._factor(
            "Serum Total Cholesterol", chol, "mg/dL",
            "< 200 mg/dL (optimal)",
            chol_status,
            (
                f"Your cholesterol of {chol} mg/dL is "
                + (
                    "in the high-risk range (≥ 240 mg/dL). Excess LDL cholesterol "
                    "deposits in arterial walls forming plaques (atherosclerosis). "
                    "This is a primary modifiable risk factor for coronary artery disease."
                    if chol >= 240
                    else "borderline high (200–239 mg/dL). While not in the danger zone, "
                    "this warrants attention alongside other risk factors."
                    if chol >= 200
                    else "within the optimal range (< 200 mg/dL), which is a positive "
                    "cardiovascular indicator."
                )
            )
        ))

        bp_status: Literal["Normal", "Borderline", "Abnormal"] = (
            "Abnormal" if trestbps >= 140 else "Borderline" if trestbps >= 120 else "Normal"
        )
        factors.append(self._factor(
            "Resting Blood Pressure", trestbps, "mmHg",
            "< 120 mmHg (normal systolic)",
            bp_status,
            (
                f"Resting systolic blood pressure of {trestbps} mmHg is "
                + (
                    "classified as Stage 2 Hypertension (≥ 140 mmHg). Chronic "
                    "hypertension forces the heart to work harder with every beat, "
                    "leading to ventricular hypertrophy and increased risk of heart "
                    "attack and stroke."
                    if trestbps >= 140
                    else "elevated (120–139 mmHg = Stage 1 / pre-hypertension). "
                    "Lifestyle changes now can prevent progression to full hypertension."
                    if trestbps >= 120
                    else "within normal range, which is an encouraging cardiovascular indicator."
                )
            )
        ))

        cp_status: Literal["Normal", "Borderline", "Abnormal"] = (
            "Normal" if cp == 3 else "Borderline" if cp == 2 else "Abnormal"
        )
        factors.append(self._factor(
            "Chest Pain Type", cp_label, f"(Type {cp})",
            "Type 3 (Non-anginal) considered least concerning",
            cp_status,
            (
                f"{cp_label} (Type {cp}): "
                + (
                    "Typical angina is chest pain caused by exertion and relieved by rest "
                    "or nitrates — a hallmark symptom of myocardial ischaemia (reduced blood "
                    "flow to the heart)."
                    if cp == 1
                    else "Atypical angina does not present with classic symptoms but is still "
                    "clinically significant and associated with coronary artery disease in many patients."
                    if cp == 2
                    else "Non-anginal chest pain is less likely to be cardiac in origin, though "
                    "other cardiac indicators must still be considered."
                    if cp == 3
                    else "Asymptomatic: the absence of classic angina does not rule out "
                    "coronary artery disease. Silent ischaemia is common, especially in "
                    "women and people with diabetes."
                )
            )
        ))

        if is_positive:
            clinical_interpretation = (
                f"As your cardiologist, I want to address your findings directly. "
                f"Your chest pain pattern ({cp_label}), combined with a resting blood "
                f"pressure of {trestbps} mmHg and cholesterol of {chol} mg/dL, "
                f"presents a constellation of cardiovascular risk factors that I take "
                f"seriously. Coronary artery disease develops over years as cholesterol "
                f"plaques slowly narrow the coronary arteries. When these arteries "
                f"become significantly narrowed, the heart muscle receives insufficient "
                f"oxygen — particularly during exertion — causing angina and, in "
                f"severe cases, myocardial infarction (heart attack). Your profile "
                f"warrants a comprehensive cardiac workup including an ECG, stress "
                f"test, echocardiogram, and coronary angiography if indicated."
            )
        else:
            clinical_interpretation = (
                f"Reviewing your cardiovascular profile, I am pleased to report "
                f"reassuring findings. Your cholesterol ({chol} mg/dL), blood "
                f"pressure ({trestbps} mmHg), and chest pain type ({cp_label}) "
                f"do not currently suggest significant coronary artery disease "
                f"based on the evaluated parameters. As a {int(age)}-year-old "
                f"{sex_label}, maintaining these values is your strongest "
                f"cardiovascular protection. Atherosclerosis is a decades-long "
                f"process — the lifestyle choices you make today directly determine "
                f"your heart health at age 60, 70, and beyond."
            )

        # ── Section 4 — Lifestyle Recommendations ──────────────────────────
        lifestyle = LifestyleRecommendations(
            diet=[
                "Adopt a Mediterranean diet: abundant olive oil, fish, legumes, nuts, vegetables, and whole grains.",
                "Reduce sodium intake to < 2,300 mg/day (< 1,500 mg if hypertensive) — sodium raises blood pressure.",
                "Eliminate trans fats and reduce saturated fats: avoid processed foods, fast food, full-fat dairy.",
                "Increase omega-3 rich foods: salmon, sardines, walnuts, flaxseed — these reduce triglycerides.",
                "Eat 5 portions of fruits and vegetables daily.",
                "Choose whole grains over refined: oats, brown rice, barley — they lower LDL cholesterol.",
            ] + ([f"With cholesterol at {chol} mg/dL, include cholesterol-lowering foods: oat bran, barley, psyllium husk, and plant sterols."] if chol >= 200 else []),
            physical_activity=[
                "150 minutes of moderate aerobic exercise weekly (walking, cycling, swimming, dancing).",
                "Aim for 75 minutes of vigorous activity (jogging, HIIT) weekly if cleared by your doctor.",
                "Include flexibility and balance training to support overall cardiovascular health.",
                "Avoid sudden intense exertion if you experience chest pain — always warm up gradually.",
            ],
            sleep=[
                "Poor sleep is independently associated with increased cardiovascular risk. Aim for 7–9 hours.",
                "Treat snoring or sleep apnoea — these cause nocturnal hypertension and cardiac stress.",
                "Maintain a consistent sleep schedule and avoid caffeine after 2 PM.",
            ],
            weight_management=[
                f"{'Reducing body weight will directly lower your blood pressure and LDL cholesterol. Even 5–10% loss makes a significant difference.' if trestbps >= 130 or chol >= 200 else 'Maintain your healthy weight through balanced nutrition and regular exercise.'}",
                "Measure waist circumference: > 94 cm (men) or > 80 cm (women) is a cardiovascular risk factor.",
            ],
            hydration=[
                "Drink 8 glasses of water daily. Adequate hydration supports blood viscosity and cardiac output.",
                "Limit caffeine to 1–2 cups daily — excess caffeine can temporarily raise blood pressure.",
                "Avoid energy drinks — they contain stimulants that can cause arrhythmias.",
            ],
            stress_management=[
                "Chronic stress releases adrenaline and cortisol, raising heart rate and blood pressure. Manage it proactively.",
                "Practise mindfulness, yoga, or progressive muscle relaxation daily.",
                "Identify toxic stressors (work, relationships, finances) and take concrete steps to address them.",
                "Maintain strong social connections — loneliness is a proven cardiovascular risk factor.",
            ],
            smoking=[
                "Smoking is the number one preventable cause of coronary heart disease. Cessation is non-negotiable.",
                "Carbon monoxide from smoke reduces oxygen in the blood. Nicotine causes arterial spasm.",
                "Within 1 year of quitting, your heart disease risk halves. After 15 years, it equals a non-smoker.",
                "Use nicotine replacement therapy, varenicline (Champix), or bupropion — all are effective.",
            ],
            alcohol=[
                "Heavy alcohol consumption raises blood pressure and triglycerides.",
                "Limit to 14 units/week (UK) or 2 units/day (men), 1 unit/day (women).",
                "Take 2–3 alcohol-free days per week and never binge drink.",
            ],
        )

        # ── Section 5 — Do's ────────────────────────────────────────────────
        if is_positive:
            dos = [
                "Seek urgent cardiology consultation within the next 1–2 weeks.",
                "Request a 12-lead ECG to assess current heart electrical activity.",
                "Ask for a stress echocardiogram or exercise stress test.",
                "Request a fasting lipid panel (LDL, HDL, total cholesterol, triglycerides).",
                "Monitor blood pressure daily with a home sphygmomanometer.",
                "Begin a cardiac-safe exercise programme only after clearance from your cardiologist.",
                "Take all prescribed cardiovascular medications exactly as directed (statins, ACE inhibitors, beta-blockers if prescribed).",
                "Keep an emergency plan: know the location of your nearest emergency department.",
                "Carry a list of your medications and medical history in your wallet.",
            ]
        else:
            dos = [
                "Schedule an annual cardiovascular health check with your GP.",
                "Monitor your blood pressure and cholesterol annually.",
                "Follow the Mediterranean diet and maintain an active lifestyle.",
                "Maintain a healthy weight and avoid smoking.",
                "Manage stress proactively with mindfulness or exercise.",
                "Know the warning signs of a heart attack (see 'When to See a Doctor').",
            ]

        # ── Section 6 — Don'ts ──────────────────────────────────────────────
        if is_positive:
            donts = [
                "Do not ignore chest pain, shortness of breath, or dizziness — seek emergency care immediately.",
                "Do not engage in sudden, strenuous exercise without medical clearance.",
                "Do not smoke or use tobacco products in any form.",
                "Do not consume high-sodium, high-saturated-fat, or processed foods.",
                "Do not miss any prescribed medication doses.",
                "Do not self-medicate or take supplements not approved by your cardiologist.",
                "Do not delay calling emergency services if you experience crushing chest pain radiating to your jaw or left arm.",
            ]
        else:
            donts = [
                "Do not smoke or start smoking.",
                "Do not overindulge in alcohol, salty foods, or saturated fats.",
                "Do not lead a sedentary lifestyle — physical inactivity is a primary cardiac risk factor.",
                "Do not ignore new-onset chest pain, palpitations, or unexplained breathlessness.",
                "Do not skip annual cardiovascular screening, especially if you have a family history of heart disease.",
            ]

        # ── Section 7 — When to See a Doctor ───────────────────────────────
        if is_positive:
            when_to_see_doctor = (
                "Please seek cardiology consultation within 1–2 weeks. "
                "Tests to request: 12-lead ECG, full lipid panel, high-sensitivity "
                "CRP, fasting glucose, renal function, echocardiogram, and stress test. "
                "CALL EMERGENCY SERVICES (999/112/911) IMMEDIATELY if you experience: "
                "crushing or squeezing chest pain (especially radiating to left arm, "
                "jaw, neck, or back), sudden severe shortness of breath, profuse cold "
                "sweating, sudden dizziness or loss of consciousness, palpitations "
                "with chest pain — these are classic symptoms of a heart attack or "
                "acute coronary syndrome."
            )
        else:
            when_to_see_doctor = (
                "Schedule a routine cardiovascular check annually with your GP. "
                "Seek prompt medical attention for: new or worsening chest pain, "
                "palpitations, unexplained breathlessness at rest or on exertion, "
                "swollen ankles (a sign of heart failure), or syncope (fainting). "
                "Call emergency services immediately for: crushing chest pain, "
                "pain radiating to the arm or jaw, or sudden severe breathlessness."
            )

        # ── Section 8 — Preventive Care ────────────────────────────────────
        preventive_care = [
            "Annual blood pressure measurement.",
            "Fasting lipid panel every 1–2 years (more frequently if elevated).",
            "Annual fasting glucose to screen for diabetes (a major cardiac risk amplifier).",
            "ECG baseline recording every 3–5 years after age 40.",
            "Body weight and waist circumference monitoring every 6 months.",
            "Smoking cessation if applicable — the single most impactful preventive measure.",
            "Aspirin therapy only if explicitly prescribed by your doctor.",
            "Statin therapy discussion with your doctor if LDL is persistently elevated.",
            "Annual influenza vaccination — flu significantly increases short-term cardiac risk.",
        ]

        # ── Section 9 — In Simple Words ────────────────────────────────────
        if is_positive:
            in_simple_words = (
                f"In simple terms: your heart is like a pump, and the pipes that "
                f"supply it with blood (coronary arteries) may be showing early signs "
                f"of blockage — a bit like limescale building up in a water pipe. "
                f"The computer looked at your chest pain pattern ({cp_label}), blood "
                f"pressure ({trestbps} mmHg), cholesterol ({chol} mg/dL), age "
                f"({int(age)}), and sex ({sex_label}), and found a pattern that looks "
                f"similar to people who have heart problems. The computer is {conf_str} "
                f"confident. This does NOT mean you are having a heart attack right now "
                f"— but it does mean you should see a heart doctor (cardiologist) soon "
                f"for proper tests. The good news: heart disease caught early can be "
                f"managed very effectively with medication and lifestyle changes."
            )
        else:
            in_simple_words = (
                f"In simple terms: the computer looked at your heart-related numbers "
                f"— your blood pressure ({trestbps} mmHg), cholesterol ({chol} mg/dL), "
                f"chest pain type ({cp_label}), age ({int(age)}), and sex ({sex_label}) "
                f"— and found that they look more like the healthy heart group. "
                f"Think of your heart as a well-maintained pump right now. Keep it "
                f"that way with regular exercise, healthy eating, not smoking, and "
                f"annual check-ups. The computer is {conf_str} confident in this "
                f"reassuring finding."
            )

        return MedicalReport(
            disease_name=self.disease_name,
            specialist_role=self.specialist_role,
            prediction_label=prediction_label,
            confidence_score=round(confidence, 4),
            risk_level=risk_level,
            prediction_summary=prediction_summary,
            explanation=explanation,
            clinical_interpretation=clinical_interpretation,
            contributing_factors=factors,
            lifestyle_recommendations=lifestyle,
            dos=dos,
            donts=donts,
            when_to_see_doctor=when_to_see_doctor,
            preventive_care=preventive_care,
            in_simple_words=in_simple_words,
            disclaimer=_DISCLAIMER,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Registry — add new diseases here
# ─────────────────────────────────────────────────────────────────────────────

REPORT_REGISTRY: dict[str, BaseReportGenerator] = {
    "breast-cancer": BreastCancerReportGenerator(),
    "diabetes": DiabetesReportGenerator(),
    "heart-disease": HeartDiseaseReportGenerator(),
}


def get_report_generator(disease_key: str) -> BaseReportGenerator:
    """
    Return the report generator for a given disease key.

    Args:
        disease_key: URL slug (e.g. "breast-cancer").

    Raises:
        KeyError: If no generator is registered for the disease key.
    """
    generator = REPORT_REGISTRY.get(disease_key)
    if generator is None:
        raise KeyError(
            f"No report generator registered for disease key '{disease_key}'. "
            f"Registered keys: {list(REPORT_REGISTRY.keys())}"
        )
    return generator
