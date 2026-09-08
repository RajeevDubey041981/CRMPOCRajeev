"""Master data for complaint model dropdown (stored in item_masters)."""

COMPLAINT_MODEL_CATEGORY = "Complaint Model"

COMPLAINT_MODEL_ITEMS: list[tuple[str, str]] = [
    ("IDC-CM-WAC", "Window AC"),
    ("IDC-CM-SAC", "Split AC"),
    ("IDC-CM-FRG", "Fridge"),
    ("IDC-CM-GYS", "Geyser"),
    ("IDC-CM-WCL", "Water Cooler"),
    ("IDC-CM-ACL", "Air Cooler"),
]
