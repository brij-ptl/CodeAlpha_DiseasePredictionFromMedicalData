import os
import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
import joblib
import urllib.request
from ucimlrepo import fetch_ucirepo

# Set up directories
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

print("Training models...")

# 1. Breast Cancer (using sklearn) - SVM
print("Training Breast Cancer Model (SVM)...")
data_bc = load_breast_cancer()
X_bc = pd.DataFrame(data_bc.data, columns=data_bc.feature_names)
y_bc = data_bc.target

# We'll select top 5 features for simplicity in the UI
features_bc = ['mean radius', 'mean texture', 'mean perimeter', 'mean area', 'mean smoothness']
X_bc_sel = X_bc[features_bc]

X_train_bc, X_test_bc, y_train_bc, y_test_bc = train_test_split(X_bc_sel, y_bc, test_size=0.2, random_state=42)

scaler_bc = StandardScaler()
X_train_bc_scaled = scaler_bc.fit_transform(X_train_bc)

svm_model = SVC(probability=True, random_state=42)
svm_model.fit(X_train_bc_scaled, y_train_bc)

joblib.dump(svm_model, os.path.join(MODEL_DIR, 'breast_cancer_model.pkl'))
joblib.dump(scaler_bc, os.path.join(MODEL_DIR, 'breast_cancer_scaler.pkl'))
print("Breast Cancer Model saved.")

# 2. Diabetes (Pima Indians) - Logistic Regression
print("Training Diabetes Model (Logistic Regression)...")
url = "https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv"
columns = ['Pregnancies', 'Glucose', 'BloodPressure', 'SkinThickness', 'Insulin', 'BMI', 'DiabetesPedigreeFunction', 'Age', 'Outcome']
df_diabetes = pd.read_csv(url, names=columns)

X_diab = df_diabetes.drop('Outcome', axis=1)
y_diab = df_diabetes['Outcome']

# Select 5 features for simplicity
features_diab = ['Pregnancies', 'Glucose', 'BloodPressure', 'BMI', 'Age']
X_diab_sel = X_diab[features_diab]

X_train_diab, X_test_diab, y_train_diab, y_test_diab = train_test_split(X_diab_sel, y_diab, test_size=0.2, random_state=42)

scaler_diab = StandardScaler()
X_train_diab_scaled = scaler_diab.fit_transform(X_train_diab)

lr_model = LogisticRegression(random_state=42)
lr_model.fit(X_train_diab_scaled, y_train_diab)

joblib.dump(lr_model, os.path.join(MODEL_DIR, 'diabetes_model.pkl'))
joblib.dump(scaler_diab, os.path.join(MODEL_DIR, 'diabetes_scaler.pkl'))
print("Diabetes Model saved.")


# 3. Heart Disease (UCI Repo) - Random Forest
print("Training Heart Disease Model (Random Forest)...")
# fetch dataset 
try:
    heart_disease = fetch_ucirepo(id=45) 
    # data (as pandas dataframes) 
    X_hd = heart_disease.data.features 
    y_hd = heart_disease.data.targets 

    # Clean data (fill NAs)
    X_hd = X_hd.fillna(X_hd.median())
    
    # Target in Cleveland is 0-4. Convert to binary: 0 = no disease, >0 = disease
    y_hd['num'] = y_hd['num'].apply(lambda x: 1 if x > 0 else 0)
    y_hd_binary = y_hd['num']

    # Select features
    features_hd = ['age', 'sex', 'cp', 'trestbps', 'chol']
    X_hd_sel = X_hd[features_hd]

    X_train_hd, X_test_hd, y_train_hd, y_test_hd = train_test_split(X_hd_sel, y_hd_binary, test_size=0.2, random_state=42)

    scaler_hd = StandardScaler()
    X_train_hd_scaled = scaler_hd.fit_transform(X_train_hd)

    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X_train_hd_scaled, y_train_hd)

    joblib.dump(rf_model, os.path.join(MODEL_DIR, 'heart_disease_model.pkl'))
    joblib.dump(scaler_hd, os.path.join(MODEL_DIR, 'heart_disease_scaler.pkl'))
    print("Heart Disease Model saved.")

except Exception as e:
    print(f"Failed to fetch Heart Disease dataset: {e}")

print("All models trained and saved successfully.")
