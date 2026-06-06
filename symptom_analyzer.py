import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import re

# ==========================
# CONFIGURATION
# ==========================

DATASET_PATH = r"C:\Users\moksh\OneDrive\Desktop\Minor project\altered_dataset_diagnosis_specific_precautions.xlsx"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

DISCLAIMER = """
⚠️ Medical Disclaimer:
This system is intended for educational and research purposes only.
It does NOT replace professional medical consultation.
Always consult a certified healthcare professional.
"""

# ==========================
# LOAD DATASET
# ==========================

df = pd.read_excel(DATASET_PATH)
df.columns = df.columns.str.strip().str.lower()
df = df.fillna("")
df = df.drop_duplicates(subset=["primary_diagnosis"])
df = df.reset_index(drop=True)

required_cols = ["primary_diagnosis", "chief_complaint"]
for col in required_cols:
    if col not in df.columns:
        raise ValueError(f"Missing required column: {col}")

# ==========================
# EMBEDDING TEXT CREATION
# ==========================

def create_embedding_text(row):
    description = row["symptoms_text"] if "symptoms_text" in df.columns else ""
    return f"Disease: {row['primary_diagnosis']},Symptoms: {row['chief_complaint']},Description: {row['symptoms_text']},Precautions: {row['precautions_cleaned']}"

df["embedding_text"] = df.apply(create_embedding_text, axis=1)

# ==========================
# DENSE RETRIEVAL (FAISS)
# ==========================

model = SentenceTransformer(EMBEDDING_MODEL)
embeddings = model.encode(df["embedding_text"].tolist(), show_progress_bar=True)
embeddings = np.array(embeddings)

dimension = embeddings.shape[1]
faiss_index = faiss.IndexFlatL2(dimension)
faiss_index.add(embeddings)

# ==========================
# SPARSE RETRIEVAL (BM25)
# ==========================

tokenized_symptoms = [
    row.lower().split() for row in df["chief_complaint"].tolist()
]
bm25 = BM25Okapi(tokenized_symptoms)

# ==========================
# SYMPTOM PROCESSING
# ==========================

def preprocess_symptoms(text):
    # Lowercase, remove extra spaces, split on comma, semicolon, or newline
    if not text:
        return set()
    items = re.split(r'[,\n;]+', text)
    return set(s.strip().lower() for s in items if s.strip())

# ==========================
# CONFIDENCE SCORING (JACCARD)
# ==========================

def confidence_score(user_symptoms, disease_symptoms):
    intersection = len(user_symptoms & disease_symptoms)
    union = len(user_symptoms | disease_symptoms)
    return (intersection / union) * 100 if union != 0 else 0

# ==========================
# EXPLAINABLE DIAGNOSIS ENGINE
# ==========================

def analyze_symptoms(user_input):

    user_symptoms = preprocess_symptoms(user_input)
    predictions = []

    for _, row in df.iterrows():

        disease_symptoms = preprocess_symptoms(row["symptoms_text"])

        matched = user_symptoms & disease_symptoms
        missing = disease_symptoms - user_symptoms

        # Jaccard similarity
        intersection = len(matched)
        union = len(user_symptoms | disease_symptoms)
        confidence = (intersection / union) * 100 if union != 0 else 0

        explanation_text = (
            f"{intersection} out of {len(disease_symptoms)} core symptoms match. "
            f"Matched: {', '.join(matched) if matched else 'None'}. "
            f"Unreported typical symptoms: {', '.join(missing) if missing else 'None'}."
        )

        predictions.append({
            "disease": row["primary_diagnosis"],
            "confidence_percentage": round(confidence, 2),
            "matched_symptoms": list(matched),
            "missing_symptoms": list(missing),
            "explanation": explanation_text,
            "description": row.get("symptoms_text", ""),
            "precautions": row.get("precautions_cleaned", "")
        })

    # Sort all diseases by confidence
    # Remove zero-confidence
    predictions = [p for p in predictions if p["confidence_percentage"] > 0]

# Sort by confidence
    predictions.sort(key=lambda x: x["confidence_percentage"], reverse=True)
    # ==============================
    # REMOVE DUPLICATE DISEASES
    # ==============================

    unique_diseases = {}

    for pred in predictions:
        disease = pred["disease"]

        if disease not in unique_diseases:
            unique_diseases[disease] = pred
        else:
            # Keep higher confidence version
            if pred["confidence_percentage"] > unique_diseases[disease]["confidence_percentage"]:
                unique_diseases[disease] = pred

    # Convert back to list
    predictions = list(unique_diseases.values())
    return {
        
        "input_symptoms": user_input,
        "all_possible_diseases_ranked": predictions,
        "disclaimer": DISCLAIMER
    }

# ==========================
# CLI INTERFACE (FOR DEMO)
# ==========================

if __name__ == "__main__":
    print("🩺 SmartMed-RAG: Explainable Medical Diagnosis System")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("Enter symptoms (comma separated): ")

        if user_input.lower() == "exit":
            break

        result = analyze_symptoms(user_input)

        print("\n🔍 Diagnosis Results\n")

        for i, pred in enumerate(result["all_possible_diseases_ranked"], 1):
            print(f"{i}. Disease: {pred['disease']}")
            print(f"   Confidence: {pred['confidence_percentage']}%")
            print(f"   Matched Symptoms: {pred['matched_symptoms']}")
            print(f"   Missing Symptoms: {pred['missing_symptoms']}")
            print(f"   Description: {pred['description']}")
            print(f"   Precautions: {pred['precautions']}\n")

        print(result["disclaimer"])
        print("=" * 50)
