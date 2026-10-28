import joblib
import numpy as np

from pathlib import Path


# ============================================================
# PROJECT PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# MODEL PATHS
# ============================================================

QUEUE_MODEL_FILE = BASE_DIR / "models" / "queue_model.joblib"
QUEUE_VECTORIZER_FILE = BASE_DIR / "models" / "queue_tfidf_vectorizer.joblib"

PRIORITY_MODEL_FILE = BASE_DIR / "models" / "priority_model.joblib"
PRIORITY_VECTORIZER_FILE = BASE_DIR / "models" / "priority_tfidf_vectorizer.joblib"


# ============================================================
# LOAD MODELS
# ============================================================

print("Loading SmartDesk AI models...")

queue_model = joblib.load(QUEUE_MODEL_FILE)
queue_vectorizer = joblib.load(QUEUE_VECTORIZER_FILE)

priority_model = joblib.load(PRIORITY_MODEL_FILE)
priority_vectorizer = joblib.load(PRIORITY_VECTORIZER_FILE)

print("All SmartDesk AI models loaded successfully.")


# ============================================================
# EXTRACT IMPORTANT TERMS
# ============================================================

def get_top_terms(model, vectorizer, features, top_n=5):

    feature_names = vectorizer.get_feature_names_out()

    coefficients = model.coef_

    predicted_class_index = list(model.classes_).index(
        model.predict(features)[0]
    )

    class_coefficients = coefficients[predicted_class_index]

    feature_values = features.toarray()[0]

    contributions = feature_values * class_coefficients

    top_indices = np.argsort(contributions)[::-1][:top_n]

    terms = []

    for index in top_indices:

        if contributions[index] > 0:

            terms.append(
                feature_names[index]
            )

    return terms


# ============================================================
# DECISION MARGIN
# ============================================================

def get_decision_margin(model, features):

    decision = model.decision_function(features)

    if np.ndim(decision) == 1:

        return float(
            abs(decision[0])
        )

    sorted_scores = np.sort(
        decision[0]
    )

    return float(
        sorted_scores[-1] - sorted_scores[-2]
    )


# ============================================================
# PREDICTION FUNCTION
# ============================================================

def predict_ticket(subject: str, body: str):

    text = f"{subject} {body}".strip()


    # ========================================================
    # QUEUE
    # ========================================================

    queue_features = queue_vectorizer.transform(
        [text]
    )

    predicted_queue = queue_model.predict(
        queue_features
    )[0]

    queue_margin = get_decision_margin(
        queue_model,
        queue_features
    )

    queue_terms = get_top_terms(
        queue_model,
        queue_vectorizer,
        queue_features
    )


    # ========================================================
    # PRIORITY
    # ========================================================

    priority_features = priority_vectorizer.transform(
        [text]
    )

    predicted_priority = priority_model.predict(
        priority_features
    )[0]

    priority_terms = get_top_terms(
        priority_model,
        priority_vectorizer,
        priority_features
    )


    # ========================================================
    # HUMAN REVIEW
    # ========================================================

    # This is a decision-margin threshold, NOT a probability.
    QUEUE_REVIEW_THRESHOLD = 0.25

    queue_review_required = (
        queue_margin < QUEUE_REVIEW_THRESHOLD
    )


    # ========================================================
    # RESULT
    # ========================================================

    return {
        "queue": predicted_queue,
        "priority": predicted_priority,

        "review_required": queue_review_required,

        "decision_margin": round(
            queue_margin,
            4
        ),

        "explanation": {
            "queue_terms": queue_terms,
            "priority_terms": priority_terms
        }
    }