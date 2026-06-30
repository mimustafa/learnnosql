STUDY_DOCUMENT = {
    "code": "HTN-REMOTE-01",
    "title": "Remote Hypertension Monitoring Study",
    "phase": "II",
    "indication": "Hypertension",
    "sites": [
        {"code": "SE-001", "country": "Sweden"},
        {"code": "US-002", "country": "United States"},
    ],
    "participants": [
        {
            "participant_id": "P-1001",
            "site_code": "SE-001",
            "cohort": "wearable-plus",
            "status": "active",
            "visits": [
                {"visit_name": "Baseline", "day": 0, "systolic_bp": 142, "heart_rate": 78},
                {"visit_name": "Week 4", "day": 28, "systolic_bp": 134, "heart_rate": 74},
            ],
        },
        {
            "participant_id": "P-1002",
            "site_code": "US-002",
            "cohort": "standard",
            "status": "active",
            "visits": [
                {"visit_name": "Baseline", "day": 0, "systolic_bp": 151, "heart_rate": 82},
                {"visit_name": "Week 4", "day": 28, "systolic_bp": 146, "heart_rate": 80},
            ],
        },
    ],
}
