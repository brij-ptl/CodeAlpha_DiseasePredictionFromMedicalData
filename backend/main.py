from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import pandas as pd
import os

app = FastAPI(title="Disease Prediction API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')

# Load models and scalers lazily
models = {}
scalers = {}

def load_model(name: str):
    if name not in models:
        model_path = os.path.join(MODEL_DIR, f'{name}_model.pkl')
        scaler_path = os.path.join(MODEL_DIR, f'{name}_scaler.pkl')
        if not os.path.exists(model_path) or not os.path.exists(scaler_path):
            raise Exception(f"Model or scaler for {name} not found. Please train models first.")
        models[name] = joblib.load(model_path)
        scalers[name] = joblib.load(scaler_path)
    return models[name], scalers[name]

class BreastCancerInput(BaseModel):
    mean_radius: float
    mean_texture: float
    mean_perimeter: float
    mean_area: float
    mean_smoothness: float

class DiabetesInput(BaseModel):
    pregnancies: float
    glucose: float
    blood_pressure: float
    bmi: float
    age: float

class HeartDiseaseInput(BaseModel):
    age: float
    sex: float
    cp: float
    trestbps: float
    chol: float

@app.post("/predict/breast-cancer")
def predict_breast_cancer(data: BreastCancerInput):
    try:
        model, scaler = load_model('breast_cancer')
        df = pd.DataFrame([data.model_dump().values()], columns=['mean radius', 'mean texture', 'mean perimeter', 'mean area', 'mean smoothness'])
        X_scaled = scaler.transform(df)
        pred = model.predict(X_scaled)[0]
        prob = model.predict_proba(X_scaled)[0][pred]
        result = "Malignant" if pred == 0 else "Benign"
        return {"prediction": result, "probability": float(prob)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/diabetes")
def predict_diabetes(data: DiabetesInput):
    try:
        model, scaler = load_model('diabetes')
        df = pd.DataFrame([data.model_dump().values()], columns=['Pregnancies', 'Glucose', 'BloodPressure', 'BMI', 'Age'])
        X_scaled = scaler.transform(df)
        pred = model.predict(X_scaled)[0]
        prob = model.predict_proba(X_scaled)[0][pred]
        result = "Positive" if pred == 1 else "Negative"
        return {"prediction": result, "probability": float(prob)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/heart-disease")
def predict_heart_disease(data: HeartDiseaseInput):
    try:
        model, scaler = load_model('heart_disease')
        df = pd.DataFrame([data.model_dump().values()], columns=['age', 'sex', 'cp', 'trestbps', 'chol'])
        X_scaled = scaler.transform(df)
        pred = model.predict(X_scaled)[0]
        prob = model.predict_proba(X_scaled)[0][pred]
        result = "Presence" if pred == 1 else "Absence"
        return {"prediction": result, "probability": float(prob)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "Disease Prediction API is running!"}
