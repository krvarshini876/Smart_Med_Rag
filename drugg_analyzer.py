import pandas as pd
from itertools import combinations

# ==========================
# LOAD DATASET
# ==========================

DATASET_PATH = r"C:\Users\keert\Downloads\Minor project (1)\Minor project\altered_dataset_diagnosis_specific_precautions.xlsx"

df = pd.read_excel(DATASET_PATH)
df.columns = df.columns.str.strip().str.lower()
df = df.fillna("")

# ==========================
# DRUG-DRUG INTERACTION TABLE
# Known interactions (drug_a, drug_b) -> warning message
# ==========================

DRUG_INTERACTIONS = {
    ("warfarin", "aspirin"):        "Increased bleeding risk.",
    ("warfarin", "ibuprofen"):      "Increased bleeding risk.",
    ("metformin", "alcohol"):       "Risk of lactic acidosis.",
    ("ssri", "tramadol"):           "Serotonin syndrome risk.",
    ("ace inhibitor", "potassium"): "Hyperkalemia risk.",
    ("statins", "erythromycin"):    "Increased statin toxicity.",
    ("digoxin", "amiodarone"):      "Digoxin toxicity risk.",
    ("methotrexate", "nsaids"):     "Methotrexate toxicity risk.",
    ("lithium", "ibuprofen"):       "Lithium toxicity risk.",
    ("clopidogrel", "omeprazole"):  "Reduced antiplatelet effect.",
}

# ==========================
# CONTRAINDICATION TABLE
# condition -> list of drugs to avoid
# ==========================

CONTRAINDICATIONS = {
    "pregnancy":      ["ibuprofen", "warfarin", "methotrexate", "tetracycline", "aspirin"],
    "kidney disease": ["nsaids", "metformin", "aminoglycosides", "lithium"],
    "liver disease":  ["paracetamol", "methotrexate", "statins", "isoniazid"],
    "asthma":         ["aspirin", "beta-blockers", "nsaids"],
    "diabetes":       ["corticosteroids", "thiazide diuretics"],
    "hypertension":   ["nsaids", "decongestants", "sympathomimetics"],
    "heart disease":  ["nsaids", "cocaine", "amphetamines"],
    "peptic ulcer":   ["aspirin", "ibuprofen", "nsaids", "corticosteroids"],
    "glaucoma":       ["anticholinergics", "corticosteroids"],
    "epilepsy":       ["tramadol", "fluoroquinolones"],
}

# ==========================
# HARDCODED DOSAGE TABLE (fallback)
# Structure per drug:
#   adult       -> standard adult dose string
#   elderly     -> dose for age > 65
#   pediatric   -> dose for age < 12  (weight-based where applicable)
#   frequency   -> how often
#   route       -> oral / IV / topical etc.
#   max_daily   -> maximum daily dose
#   notes       -> extra clinical notes
# ==========================

DRUG_DOSAGE_TABLE = {
    "paracetamol": {
        "adult":     "500 mg – 1000 mg per dose",
        "elderly":   "500 mg per dose (use lower end)",
        "pediatric": "15 mg/kg per dose",
        "frequency": "Every 4–6 hours",
        "route":     "Oral / IV",
        "max_daily": "4000 mg/day (adult); 60 mg/kg/day (child)",
        "notes":     "Do not exceed max dose; avoid in liver disease.",
    },
    "ibuprofen": {
        "adult":     "200 mg – 400 mg per dose",
        "elderly":   "200 mg per dose; use with caution",
        "pediatric": "5–10 mg/kg per dose",
        "frequency": "Every 6–8 hours",
        "route":     "Oral",
        "max_daily": "1200 mg/day (OTC); 2400 mg/day (prescription)",
        "notes":     "Take with food. Avoid in kidney disease, peptic ulcer, asthma.",
    },
    "aspirin": {
        "adult":     "325 mg – 650 mg per dose (pain); 75–100 mg/day (cardio)",
        "elderly":   "75–100 mg/day for cardiovascular use",
        "pediatric": "NOT recommended under 16 (Reye's syndrome risk)",
        "frequency": "Every 4–6 hours (pain); Once daily (cardio)",
        "route":     "Oral",
        "max_daily": "4000 mg/day",
        "notes":     "Avoid in children, peptic ulcer, bleeding disorders.",
    },
    "amoxicillin": {
        "adult":     "250 mg – 500 mg per dose",
        "elderly":   "250 mg – 500 mg per dose (adjust if renal impairment)",
        "pediatric": "25 mg/kg/day divided every 8 hours",
        "frequency": "Every 8 hours",
        "route":     "Oral",
        "max_daily": "3000 mg/day",
        "notes":     "Complete full course. Check for penicillin allergy.",
    },
    "metformin": {
        "adult":     "500 mg – 1000 mg per dose",
        "elderly":   "500 mg per dose; monitor renal function",
        "pediatric": "500 mg once daily (>10 yrs only)",
        "frequency": "Twice daily with meals",
        "route":     "Oral",
        "max_daily": "2000–2550 mg/day",
        "notes":     "Hold before contrast procedures. Avoid in kidney disease.",
    },
    "atorvastatin": {
        "adult":     "10 mg – 80 mg once daily",
        "elderly":   "Start at 10 mg; titrate slowly",
        "pediatric": "10 mg once daily (>10 yrs, familial hypercholesterolaemia)",
        "frequency": "Once daily (evening preferred)",
        "route":     "Oral",
        "max_daily": "80 mg/day",
        "notes":     "Monitor liver enzymes. Avoid with erythromycin/clarithromycin.",
    },
    "omeprazole": {
        "adult":     "20 mg – 40 mg per dose",
        "elderly":   "20 mg per dose",
        "pediatric": "0.7–3.3 mg/kg/day",
        "frequency": "Once daily (before breakfast)",
        "route":     "Oral / IV",
        "max_daily": "40 mg/day",
        "notes":     "Long-term use may reduce B12 / magnesium. Review need regularly.",
    },
    "warfarin": {
        "adult":     "2 mg – 10 mg once daily (INR-guided)",
        "elderly":   "Start at 2 mg; highly sensitive — monitor INR closely",
        "pediatric": "0.1 mg/kg/day (specialist use only)",
        "frequency": "Once daily",
        "route":     "Oral",
        "max_daily": "Individualised to INR target",
        "notes":     "Many interactions. Regular INR monitoring essential.",
    },
    "metoprolol": {
        "adult":     "25 mg – 100 mg per dose",
        "elderly":   "25 mg per dose; titrate slowly",
        "pediatric": "1–2 mg/kg/day (specialist use)",
        "frequency": "Once or twice daily",
        "route":     "Oral",
        "max_daily": "200 mg/day",
        "notes":     "Do not stop abruptly. Avoid in asthma / COPD.",
    },
    "amlodipine": {
        "adult":     "5 mg – 10 mg once daily",
        "elderly":   "2.5 mg – 5 mg once daily",
        "pediatric": "0.1–0.3 mg/kg once daily (specialist use)",
        "frequency": "Once daily",
        "route":     "Oral",
        "max_daily": "10 mg/day",
        "notes":     "May cause ankle oedema. Do not stop abruptly.",
    },
    "salbutamol": {
        "adult":     "100–200 mcg (1–2 puffs) per dose",
        "elderly":   "100 mcg (1 puff); use spacer if coordination poor",
        "pediatric": "100 mcg (1 puff); use spacer device",
        "frequency": "Every 4–6 hours as needed",
        "route":     "Inhaled",
        "max_daily": "800–1600 mcg/day",
        "notes":     "Reliever inhaler only. Overuse indicates poor control.",
    },
    "prednisolone": {
        "adult":     "5 mg – 60 mg per dose (condition-dependent)",
        "elderly":   "Use lowest effective dose; osteoporosis risk",
        "pediatric": "1–2 mg/kg/day (max 40 mg)",
        "frequency": "Once daily (morning)",
        "route":     "Oral",
        "max_daily": "Condition-dependent",
        "notes":     "Taper dose on stopping long-term use. Monitor blood glucose.",
    },
    "ciprofloxacin": {
        "adult":     "250 mg – 750 mg per dose",
        "elderly":   "250 mg – 500 mg per dose",
        "pediatric": "Not recommended routinely (cartilage risk)",
        "frequency": "Every 12 hours",
        "route":     "Oral / IV",
        "max_daily": "1500 mg/day (oral)",
        "notes":     "Take on empty stomach. Avoid antacids within 2 hrs.",
    },
    "lisinopril": {
        "adult":     "5 mg – 40 mg once daily",
        "elderly":   "Start at 2.5 mg; monitor renal function and potassium",
        "pediatric": "0.07 mg/kg once daily (specialist use)",
        "frequency": "Once daily",
        "route":     "Oral",
        "max_daily": "40 mg/day",
        "notes":     "May cause dry cough. Avoid in pregnancy. Monitor potassium.",
    },
    "diazepam": {
        "adult":     "2 mg – 10 mg per dose",
        "elderly":   "2 mg per dose; high fall risk",
        "pediatric": "0.1–0.3 mg/kg (acute use only)",
        "frequency": "2–4 times daily (short-term only)",
        "route":     "Oral / IV / Rectal",
        "max_daily": "30 mg/day",
        "notes":     "Risk of dependence. Short-term use only. Avoid with alcohol.",
    },
    "insulin": {
        "adult":     "Individualised — typically 0.5–1 unit/kg/day total",
        "elderly":   "Lower doses; higher hypoglycaemia risk",
        "pediatric": "0.5–1 unit/kg/day; specialist supervision required",
        "frequency": "Varies by insulin type (basal / bolus)",
        "route":     "Subcutaneous / IV",
        "max_daily": "Individualised",
        "notes":     "Monitor blood glucose closely. Adjust for meals and activity.",
    },
    "hydroxychloroquine": {
        "adult":     "200 mg – 400 mg once daily",
        "elderly":   "200 mg once daily",
        "pediatric": "5 mg/kg/day (max 400 mg)",
        "frequency": "Once daily with food",
        "route":     "Oral",
        "max_daily": "400 mg/day",
        "notes":     "Regular eye exams needed. Takes weeks for full effect.",
    },
    "azithromycin": {
        "adult":     "500 mg on day 1, then 250 mg days 2–5",
        "elderly":   "Same as adult; use with caution in cardiac patients",
        "pediatric": "10 mg/kg on day 1, then 5 mg/kg days 2–5",
        "frequency": "Once daily",
        "route":     "Oral",
        "max_daily": "500 mg/day",
        "notes":     "QT prolongation risk. Check interactions.",
    },
    "pantoprazole": {
        "adult":     "20 mg – 40 mg per dose",
        "elderly":   "20 mg per dose",
        "pediatric": "Not established under 5 yrs",
        "frequency": "Once daily (before breakfast)",
        "route":     "Oral / IV",
        "max_daily": "40 mg/day",
        "notes":     "Similar to omeprazole. Review need periodically.",
    },
    "tramadol": {
        "adult":     "50 mg – 100 mg per dose",
        "elderly":   "50 mg per dose; increased seizure and fall risk",
        "pediatric": "Not recommended under 12",
        "frequency": "Every 4–6 hours",
        "route":     "Oral / IV",
        "max_daily": "400 mg/day",
        "notes":     "Risk of dependence. Avoid with SSRIs (serotonin syndrome).",
    },
}


def get_dosage_recommendation(drug, patient):
    """
    Look up drug-specific dosage.
    Priority: dataset column 'dosage' -> DRUG_DOSAGE_TABLE -> generic fallback.
    """
    age    = patient.get("age", 30)
    weight = patient.get("weight_kg", 70)

    # --- 1. Try dataset column first ---
    dataset_dosage = ""
    drug_lower = drug.strip().lower()

    if "dosage" in df.columns:
        match = df[df["medications"].str.lower().str.strip() == drug_lower]
        if match.empty and "drug" in df.columns:
            match = df[df["drug"].str.lower().str.strip() == drug_lower]
        if not match.empty:
            dataset_dosage = str(match.iloc[0].get("dosage", "")).strip()

    if dataset_dosage and dataset_dosage not in ("", "nan"):
        source = "[Source: your dataset]"
        return f"{dataset_dosage}  {source}"

    # --- 2. Fallback: hardcoded table (fuzzy key match) ---
    matched_key = None
    for key in DRUG_DOSAGE_TABLE:
        if key in drug_lower or drug_lower in key:
            matched_key = key
            break

    if matched_key:
        d = DRUG_DOSAGE_TABLE[matched_key]

        if age < 12:
            dose_str = d["pediatric"]
            tier     = "Pediatric"
        elif age > 65:
            dose_str = d["elderly"]
            tier     = "Elderly"
        else:
            dose_str = d["adult"]
            tier     = "Adult"

        # Weight note
        weight_note = ""
        if age < 12:
            weight_note = f" (Patient weight: {weight} kg — apply weight-based calculation above.)"
        elif weight < 50:
            weight_note = " (Low body weight: consider dose reduction.)"
        elif weight > 120:
            weight_note = " (High body weight: standard dose may need upward adjustment.)"

        lines = [
            f"[Source: drug database]  Tier: {tier}",
            f"  Dose      : {dose_str}{weight_note}",
            f"  Frequency : {d['frequency']}",
            f"  Route     : {d['route']}",
            f"  Max/day   : {d['max_daily']}",
            f"  Notes     : {d['notes']}",
        ]
        return "\n".join(lines)

    # --- 3. Generic fallback ---
    tier = "Pediatric" if age < 12 else ("Elderly" if age > 65 else "Adult")
    return (
        f"[Source: generic estimate]  No specific dosage data found for '{drug}'.\n"
        f"  Tier: {tier}. Consult prescribing guidelines or a pharmacist.\n"
        f"  Weight: {weight} kg — use weight-based calculation if applicable."
    )

# ==========================
# CHECK DRUG-DRUG INTERACTIONS
# ==========================

def check_interactions(drug_list):
    interactions_found = []
    normalized = [d.strip().lower() for d in drug_list if d.strip()]

    for drug_a, drug_b in combinations(normalized, 2):
        for (a, b), warning in DRUG_INTERACTIONS.items():
            if (a in drug_a or a in drug_b) and (b in drug_a or b in drug_b):
                interactions_found.append(
                    f"Interaction between '{drug_a}' and '{drug_b}': {warning}"
                )

    return list(set(interactions_found))

# ==========================
# CHECK CONTRAINDICATIONS
# ==========================

def check_contraindications(drug, patient_conditions):
    flags = []
    drug_lower = drug.strip().lower()

    for condition in patient_conditions:
        condition_lower = condition.strip().lower()
        banned_drugs = CONTRAINDICATIONS.get(condition_lower, [])
        for banned in banned_drugs:
            if banned in drug_lower or drug_lower in banned:
                flags.append(
                    f"[CONTRAINDICATED] '{drug}' is contraindicated in patients with {condition}."
                )
    return flags

# ==========================
# PREPROCESS FUNCTION
# ==========================

def preprocess(text):
    return set(t.strip().lower() for t in str(text).split(",") if t.strip())

# ==========================
# MAIN DRUG ANALYZER
# ==========================

def analyze_drug(user_input, patient=None):
    """
    Parameters
    ----------
    user_input : str
        Comma-separated symptom list entered by the user.
    patient    : dict (optional)
        Keys: age (int), weight_kg (float), conditions (list of str)
        e.g. {"age": 70, "weight_kg": 65, "conditions": ["kidney disease", "hypertension"]}
    """
    if patient is None:
        patient = {"age": 30, "weight_kg": 70, "conditions": []}

    patient_conditions = patient.get("conditions", [])
    user_symptoms = preprocess(user_input)
    results = []

    for _, row in df.iterrows():
        disease    = row.get("primary_diagnosis", "")
        symptoms   = preprocess(row.get("chief_complaint", ""))
        drug       = row.get("medications", "") or row.get("drug", "")
        precautions = row.get("precautions", "") or row.get("precautions_cleaned", "")

        matched  = user_symptoms & symptoms
        missing  = symptoms - user_symptoms

        intersection = len(matched)
        union        = len(user_symptoms | symptoms)
        confidence   = (intersection / union) * 100 if union != 0 else 0

        if confidence > 0:
            dosage_note  = get_dosage_recommendation(drug, patient)
            contra_flags = check_contraindications(drug, patient_conditions)

            explanation = (
                f"{intersection} symptom(s) matched with {disease}. "
                f"Matched: {', '.join(matched) if matched else 'None'}. "
                f"Missing: {', '.join(missing) if missing else 'None'}."
            )

            results.append({
                "disease":           disease,
                "drug":              drug,
                "precautions":       precautions,
                "confidence":        round(confidence, 2),
                "matched_symptoms":  list(matched),
                "explanation":       explanation,
                "dosage_note":       dosage_note,
                "contraindications": contra_flags,
            })

    results.sort(key=lambda x: x["confidence"], reverse=True)

    # Deduplicate by disease (keep highest confidence)
    unique = {}
    for res in results:
        disease = res["disease"]
        if disease not in unique or res["confidence"] > unique[disease]["confidence"]:
            unique[disease] = res

    top_results = list(unique.values())[:3]

    # Drug-drug interaction check across top results
    top_drugs    = [r["drug"] for r in top_results if r["drug"]]
    interactions = check_interactions(top_drugs)
    for res in top_results:
        res["drug_interactions"] = interactions

    return top_results

# ==========================
# CLI ENTRY POINT
# ==========================

if __name__ == "__main__":
    print("Drug Analyzer -- Enhanced Edition")
    print("Type 'exit' to quit\n")

    # Collect patient profile once at startup
    print("Patient Profile Setup (press Enter to use defaults)")
    try:
        age_in = input("   Age (default 30): ").strip()
        age    = int(age_in) if age_in else 30

        wt_in  = input("   Weight in kg (default 70): ").strip()
        weight = float(wt_in) if wt_in else 70.0

        cond_in    = input("   Known conditions e.g. 'diabetes, asthma' (default none): ").strip()
        conditions = [c.strip().lower() for c in cond_in.split(",") if c.strip()] if cond_in else []
    except ValueError:
        print("   Invalid input -- using defaults.\n")
        age, weight, conditions = 30, 70.0, []

    patient = {"age": age, "weight_kg": weight, "conditions": conditions}
    print(f"\nProfile set -- Age: {age}, Weight: {weight} kg, Conditions: {conditions or 'None'}\n")
    print("=" * 60)

    while True:
        user_input = input("\nEnter symptoms (comma-separated): ").strip()

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        results = analyze_drug(user_input, patient=patient)

        if not results:
            print("No results found.\n")
            continue

        print("\nDrug Analysis Results:\n")

        for i, res in enumerate(results, 1):
            print(f"{'='*60}")
            print(f"  {i}. Disease     : {res['disease']}")
            print(f"     Drug        : {res['drug']}")
            print(f"     Confidence  : {res['confidence']}%")
            print(f"     Precautions : {res['precautions']}")
            print(f"     Match Info  : {res['explanation']}")

            print(f"\n     Dosage Guidance:")
            print(f"        {res['dosage_note']}")

            if res["contraindications"]:
                print(f"\n     Contraindications:")
                for flag in res["contraindications"]:
                    print(f"        {flag}")
            else:
                print(f"\n     No contraindications detected for this patient profile.")

            if res["drug_interactions"]:
                print(f"\n     Drug-Drug Interactions (across top results):")
                for interaction in res["drug_interactions"]:
                    print(f"        {interaction}")
            else:
                print(f"\n     No drug-drug interactions detected among top results.")

        print(f"{'='*60}")
