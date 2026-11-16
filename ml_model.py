
"""
HealthCare Personal Portal
Educational Health Risk Classification Model

Note: This is a demonstration model, not a clinical diagnostic tool.
"""

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import numpy as np


# Synthetic educational sample data.
# Features: age, BMI, systolic BP, glucose, exercise days/week, smoking
def create_demo_dataset():
    rng = np.random.default_rng(42)
    samples = 1200

    age = rng.integers(18, 81, samples)
    bmi = rng.uniform(16, 42, samples)
    systolic_bp = rng.integers(90, 191, samples)
    glucose = rng.integers(65, 221, samples)
    exercise_days = rng.integers(0, 8, samples)
    smoking = rng.integers(0, 2, samples)

    # Simple illustrative rules create labels for the demo dataset.
    # This is not a medically validated risk formula.
    score = (
        (age >= 50).astype(int)
        + (bmi >= 30).astype(int)
        + (systolic_bp >= 140).astype(int) * 2
        + (glucose >= 140).astype(int) * 2
        + smoking
        - (exercise_days >= 4).astype(int)
    )

    risk = np.where(score <= 1, "Low",
            np.where(score <= 3, "Moderate", "High"))

    X = np.column_stack((
        age, bmi, systolic_bp, glucose, exercise_days, smoking
    ))
    return X, risk


X, y = create_demo_dataset()

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

model = Pipeline([
    ("scaler", StandardScaler()),
    ("classifier", RandomForestClassifier(
        n_estimators=150,
        random_state=42,
        class_weight="balanced"
    ))
])

model.fit(X_train, y_train)

MODEL_ACCURACY = accuracy_score(y_test, model.predict(X_test))


def predict_health_risk(
    age,
    bmi,
    systolic_bp,
    glucose,
    exercise_days,
    smoking
):
    """Return a demo risk category and model confidence."""

    values = [
        age,
        bmi,
        systolic_bp,
        glucose,
        exercise_days,
        smoking
    ]

    if not 1 <= age <= 120:
        raise ValueError("Age must be between 1 and 120.")

    if not 10 <= bmi <= 80:
        raise ValueError("BMI must be between 10 and 80.")

    if not 50 <= systolic_bp <= 300:
        raise ValueError("Systolic blood pressure is outside the accepted input range.")

    if not 30 <= glucose <= 600:
        raise ValueError("Glucose is outside the accepted input range.")

    if not 0 <= exercise_days <= 7:
        raise ValueError("Exercise days must be between 0 and 7.")

    if smoking not in (0, 1):
        raise ValueError("Smoking must be 0 (No) or 1 (Yes).")

    prediction = model.predict([values])[0]
    probabilities = model.predict_proba([values])[0]
    confidence = float(max(probabilities) * 100)

    return {
        "risk": str(prediction),
        "confidence": round(confidence, 1),
        "model_accuracy": round(float(MODEL_ACCURACY) * 100, 1)
    }


if __name__ == "__main__":
    print("Health Risk Classification Model")
    print(f"Demo test accuracy: {MODEL_ACCURACY * 100:.2f}%")

    result = predict_health_risk(
        age=35,
        bmi=23.5,
        systolic_bp=115,
        glucose=90,
        exercise_days=5,
        smoking=0
    )

    print("Sample prediction:", result)