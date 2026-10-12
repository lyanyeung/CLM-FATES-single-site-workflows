from pathlib import Path
import pandas as pd
import json

ROOT = Path(
    "/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"
)

SITES = [
    "CZ-BK1", "IT-Ren", "FR-Hes", "FR-FBn",
    "DE-Hzd", "CH-Dav", "BE-Vie", "IT-Lav"
]

summary = []

for site in SITES:
    qc = ROOT / site / "forcing/qc_v5"

    status_file = qc / f"{site}_status.json"
    events_file = qc / f"{site}_replacement_events.csv"
    review_file = qc / f"{site}_manual_review.csv"

    print(f"\n{'='*75}")
    print(f"SITE: {site}")
    print(f"{'='*75}")

    status = json.loads(status_file.read_text())
    events = pd.read_csv(events_file)
    reviews = pd.read_csv(review_file)

    events["official_qc"] = pd.to_numeric(
        events["official_qc"], errors="coerce"
    )

    qc0 = events[events["official_qc"] == 0]

    print("Status:", status["status"])
    print("Total modifications:", len(events))
    print("Modified official QC=0:", len(qc0))
    print("Manual reviews:", len(reviews))

    if len(events):
        print("\nModification reasons:")
        print(events["reason"].value_counts().to_string())

    if len(qc0):
        print("\nIMPORTANT: OFFICIAL QC=0 MODIFICATIONS")
        print(qc0[
            ["time", "variable", "original_value",
             "final_value", "reason"]
        ].to_string(index=False, max_rows=30))

    if len(reviews):
        print("\nMANUAL REVIEW DETAILS:")
        print(reviews[
            ["time", "variable", "final_value",
             "era_value", "official_qc", "reason"]
        ].to_string(index=False))

    summary.append({
        "site": site,
        "status": status["status"],
        "modifications": len(events),
        "modified_official_QC0": len(qc0),
        "manual_reviews": len(reviews)
    })

out = Path.home() / "eight_site_qc_final_audit.csv"
df = pd.DataFrame(summary)
df.to_csv(out, index=False)

print("\n============== FINAL SUMMARY ==============")
print(df.to_string(index=False))
print("\nSaved:", out)
