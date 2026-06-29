STUDY = {
    "study_id": "EHEALTH-101",
    "title": "Remote Blood Pressure Coaching Trial",
    "condition": "Hypertension",
    "phase": "Pilot randomized trial",
    "status": "recruiting",
    "protocol": {
        "version": "2.1",
        "consent": ["eConsent", "wearable data sharing", "telehealth follow-up"],
        "visit_schedule": [
            {"code": "baseline", "label": "Baseline", "day": 0},
            {"code": "week_2", "label": "Week 2", "day": 14},
            {"code": "week_8", "label": "Week 8", "day": 56},
        ],
        "primary_outcome": "Mean systolic blood pressure change at week 8",
    },
    "sites": [
        {"site_id": "S-01", "name": "Uppsala Digital Clinic", "country": "SE"},
        {"site_id": "S-02", "name": "Boston Telehealth Center", "country": "US"},
    ],
}

PARTICIPANTS = [
    {
        "participant_id": "P-1001",
        "study_id": "EHEALTH-101",
        "site_id": "S-01",
        "cohort": "coaching_app",
        "profile": {"age": 52, "sex": "female", "risk_group": "high"},
        "devices": [
            {"type": "blood_pressure_cuff", "vendor": "Omron", "paired": True},
            {"type": "activity_tracker", "vendor": "Fitbit", "paired": True},
        ],
        "visits": [
            {
                "visit_code": "baseline",
                "completed_at": "2026-01-10",
                "mode": "telehealth",
                "measurements": {
                    "systolic_bp": 151,
                    "diastolic_bp": 93,
                    "steps_7_day_avg": 4200,
                    "phq4_score": 5,
                },
                "questionnaires": [
                    {"name": "Medication adherence", "score": 7},
                    {"name": "Digital literacy", "score": 4},
                ],
                "adverse_events": [],
            },
            {
                "visit_code": "week_2",
                "completed_at": "2026-01-24",
                "mode": "app_check_in",
                "measurements": {
                    "systolic_bp": 144,
                    "diastolic_bp": 88,
                    "steps_7_day_avg": 5100,
                    "coach_messages_read": 11,
                },
                "questionnaires": [{"name": "Medication adherence", "score": 8}],
                "adverse_events": [],
            },
        ],
    },
    {
        "participant_id": "P-1002",
        "study_id": "EHEALTH-101",
        "site_id": "S-02",
        "cohort": "usual_care",
        "profile": {"age": 61, "sex": "male", "risk_group": "medium"},
        "devices": [{"type": "blood_pressure_cuff", "vendor": "Withings", "paired": True}],
        "visits": [
            {
                "visit_code": "baseline",
                "completed_at": "2026-01-12",
                "mode": "clinic",
                "measurements": {
                    "systolic_bp": 148,
                    "diastolic_bp": 91,
                    "steps_7_day_avg": 3900,
                    "phq4_score": 2,
                },
                "questionnaires": [{"name": "Medication adherence", "score": 6}],
                "adverse_events": [],
            }
        ],
    },
]
