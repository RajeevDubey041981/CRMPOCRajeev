"""Import Indcool product catalogue from the CSV export.

Run from the api/ directory:
    python scripts/import_items.py

Behaviour:
  - Items whose item_code already exists are UPDATED with the CSV name/category.
  - Items with no barcode get a synthetic code  IDC-{original_prod_id}.
  - Duplicate barcodes in the source get a suffix  {code}-{original_id}.
  - Deleted-at is left untouched for existing rows; new rows default to active.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select

from app.database import SessionLocal
from app.models.item_master import ItemMaster

# ---------------------------------------------------------------------------
# Source data  (original_prod_id, item_code_or_blank, item_name)
# ---------------------------------------------------------------------------
ITEMS_RAW = [
    (6,   "8908012210436",              "SPLIT AC IDCACS18K5"),
    (7,   "8908012210412",              "SPLIT AC IDCACI18K3"),
    (8,   "8908012210429",              "SPLIT AC IDCACI018K3"),
    (12,  "8908012210467",              "SPLIT AC IDCACSN18K5"),
    (13,  "8908012210450",              "SPLIT AC IDCACSN18K3"),
    (14,  "8908012210481",              "SPLIT AC IDCACSN13K5"),
    (15,  "8908012210474",              "SPLIT AC IDCACS13K3"),
    (16,  "8908012210511",              "SPLIT AC IDCACS24K5I"),
    (17,  "8908012210528",              "SPLIT AC IDCACS24K3I"),
    (18,  "8908012210542",              "SPLIT AC IDCACSG18K5"),
    (19,  "8908012210573",              "SPLIT AC IDCACSE18K5"),
    (20,  "8908012210566",              "SPLIT AC IDCACSE13K3"),
    (21,  "8908012210610",              "SPLIT AC IDCACSG13K5"),
    (22,  "8908012210801",              "SPLIT AC IDCACSE24K5I"),
    (23,  "8908012210726",              "SPLIT AC IDCACS24K5INV"),
    (25,  "8908012210634",              "SPLIT AC IDCACHC18K5"),
    (26,  "",                           "SPLIT AC IDCACHC18K3"),
    (27,  "",                           "WINDOW AC IDCACW18K3"),
    (28,  "8908012210597",              "WINDOW AC IDCACW18K5INV"),
    (29,  "",                           "WINDOW AC IDCACW13K5I"),
    (30,  "8908012210764",              "WINDOW AC IDCACW24K5I"),
    (31,  "8908012210627",              "WINDOW AC IDCACW12K5I"),
    (32,  "8908012210443",              "SPLIT AC IDCACS24K3F"),
    (34,  "8908012210498",              "SPLIT AC IDCACSN18K3F"),
    (35,  "8908012210504",              "WINDOW AC IDCACW18K3F"),
    (36,  "8908012210535",              "WINDOW AC IDCACW18K5F"),
    (37,  "8908012210559",              "WINDOW AC IDCACWN18K5F"),
    (38,  "8908012210689",              "WINDOW AC IDCACWN18K3F"),
    (39,  "8908012210603",              "WINDOW AC IDCACW24K3F"),
    (40,  "",                           "WINDOW AC IDCACWN24KF"),
    (41,  "",                           "CASSETTE AC IDCACFS48KINV"),
    (42,  "",                           "TOWER AC IDCACFSS48KINV"),
    (43,  "",                           "WATER HEATER IDCWH5-10"),
    (44,  "",                           "WATER HEATER IDCWH5-15"),
    (45,  "",                           "WATER HEATER IDCWH5-25"),
    (46,  "",                           "WATER HEATER IDCWH5-35"),
    (47,  "",                           "WATER HEATER IDCWH5-50"),
    (48,  "",                           "WATER HEATER IDCWH-15H"),
    (49,  "",                           "WATER HEATER IDCWH-25H"),
    (50,  "",                           "WATER HEATER IDCWH510SV"),
    (51,  "",                           "WATER HEATER IDCWH515GV"),
    (52,  "",                           "WATER HEATER IDCWH515SV"),
    (53,  "",                           "WATER HEATER IDCWH525GV"),
    (54,  "",                           "WATER HEATER IDCWH525SV"),
    (55,  "",                           "EXHAUST FAN IDCEF12"),
    (56,  "",                           "CEILING FAN IDCCF500"),
    (57,  "",                           "CEILING FAN IDCCF600"),
    (58,  "",                           "CEILING FAN IDCCF115"),
    (59,  "",                           "CEILING FAN IDCCF112"),
    (61,  "",                           "CEILING FAN IDCCF113"),
    (62,  "",                           "CEILING FAN IDCCF116"),
    (64,  "",                           "CEILING FAN IDCCF1000"),
    (65,  "",                           "CEILING FAN IDCCF120"),
    (66,  "",                           "CEILING FAN IDCCF50"),
    (67,  "",                           "GEYSER IDCWH5-35"),
    (68,  "",                           "GEYSER IDCWH5-50"),
    (69,  "",                           "GEYSER IDCWH510SV"),
    (70,  "",                           "GEYSER IDCWH515GV"),
    (71,  "",                           "GEYSER DCWH515SV"),
    (72,  "",                           "GEYSER IDCWH525GV"),
    (73,  "",                           "GEYSER IDCWH525SV"),
    (74,  "",                           "WATER COOLER IDCWC FSS150/150"),
    (75,  "8908012210771",              "IDCACS18K5HE"),
    (76,  "8908012210849",              "IDCACSD18K5"),
    (79,  "",                           "IDCEF 15E (INDCOOL)"),
    (82,  "",                           "EXHAUST FAN IDC TA 12 INDCOOL"),
    (83,  "",                           "IEDEF12E INDCOOL"),
    (84,  "",                           "IDC EF 9 INDCOOL"),
    (85,  "",                           "IEDEF 12E INDCOOL"),
    (86,  "",                           "IDC EF 9 INDCOOL (2)"),
    (88,  "",                           "IDCACBF18K3EF"),
    (89,  "8908012210894",              "IDCACSBF18K5G"),
    (90,  "8908012210610",              "IDCACSG13K5"),      # dup barcode → gets suffix
    (91,  "",                           "IDCACBF18K5EF"),
    (92,  "",                           "IDCACC24K3AIN"),
    (93,  "Winora IDCREFSD190D3SPW",    "REF DC 190L Winora IDCREFSD190D3"),
    (94,  "AQUA FLORA IDCREFSD190D3CFB","REF DC 190L AQUA FLORA IDCREFSD190D3"),
    (95,  "",                           "IDCREFSD190D1CFB"),
    (97,  "IDCAMCA012",                 "AMC Assurance Plan 12 MONTHS AGE 0-12"),
    (98,  "IDCAMCC012",                 "AMC Comprehensive Plan 12 MONTHS AGE 0-12"),
    (99,  "IDCAMCC024",                 "AMC Comprehensive Plan 24 MONTHS AGE 0-12"),
    (100, "IDCAMCC036",                 "AMC Comprehensive Plan 36 MONTHS AGE 0-12"),
    (101, "IDCAMCC048",                 "AMC Comprehensive Plan 48 MONTHS AGE 0-12"),
    (102, "IDCAMCC1312",                "AMC Comprehensive Plan 12 MONTHS AGE 13-24"),
    (103, "IDCAMCC1324",                "AMC Comprehensive Plan 24 MONTHS AGE 13-24"),
    (104, "IDCAMCC1336",                "AMC Comprehensive Plan 36 MONTHS AGE 13-24"),
    (105, "IDCAMCC2512",                "AMC Comprehensive Plan 12 MONTHS AGE 25-36"),
    (106, "IDCAMCC2524",                "AMC Comprehensive Plan 24 MONTHS AGE 25-36"),
    (107, "IDCAMCC3612",                "AMC Comprehensive Plan 12 MONTHS AGE 36-48"),
    (108, "",                           "IDCACSBF22K5"),
    (109, "8908012210924",              "IDCACSBF16K5"),
    (110, "",                           "IDCACSBF16K3"),
    (111, "",                           "IDCACSBF10K3"),
    (112, "",                           "IDCACSBF10K5"),
    (113, "",                           "IDCACSBF16K5 (2)"),  # dup name
    (115, "8908012210917",              "IDCACSBFS24K5INV"),
    (116, "8908012210931",              "SPLIT AC IDCACS13K3E"),
    (117, "8908012210948",              "SPLIT AC IDCACS24K5E"),
    (118, "8908012210955",              "WINDOW AC IDCACW24K3E"),
    (119, "8908012210962",              "GEYSER IDCWH35L"),
    (120, "8908012210979",              "FRIDGE IDCFRD360L"),
    (121, "8908012210986",              "AIR COOLER IDCCLR80L"),
    (122, "8908012210993",              "SPLIT AC IDCACS13K3E"),
    (123, "8908012211006",              "WINDOW AC IDCACW24K3E"),
]


def detect_category(item_name: str) -> str | None:
    n = item_name.upper().strip()
    plain = n.replace(" ", "").replace("-", "")

    # Keyword-based (most reliable)
    if "SPLIT AC" in n:
        return "Split AC"
    if "WINDOW AC" in n:
        return "Window AC"
    if "CASSETTE AC" in n:
        return "Cassette AC"
    if "TOWER AC" in n:
        return "Duct AC"
    if "WATER HEATER" in n or "GYSER" in n or "GEYSER" in n:
        return "Geyser"
    if "EXHAUST FAN" in n or "CEILING FAN" in n or "CELLING FAN" in n:
        return "Accessory"
    if "WATER COOLER" in n:
        return "Others"
    if "REF DC" in n:
        return "Refrigerator"
    if n.startswith("AMC ") or plain.startswith("IDCAMCA") or plain.startswith("IDCAMCC"):
        return "Others"

    # Code-prefix-based
    if plain.startswith("IDCACW"):
        return "Window AC"
    if plain.startswith("IDCACC"):
        return "Cassette AC"
    if plain.startswith("IDCACF"):
        return "Cassette AC"
    if plain.startswith("IDCAC"):
        return "Split AC"           # all remaining IDCAC* are split variants
    if plain.startswith("IDCWH") or plain.startswith("DCWH"):
        return "Geyser"
    if plain.startswith("IDCWC"):
        return "Others"
    if plain.startswith("IDCREF"):
        return "Refrigerator"
    if plain.startswith("IDCCF"):
        return "Accessory"          # ceiling fans
    if plain.startswith("IDCEF") or plain.startswith("IEDEF"):
        return "Accessory"          # exhaust fans
    if "IDCEF" in plain or "IDC EF" in n or "IDC TA" in n:
        return "Accessory"

    return None


def resolve_code(original_id: int, raw_code: str, seen: set) -> str:
    code = raw_code.strip()
    if not code:
        code = f"IDC-{original_id}"
    if code in seen:
        code = f"{code}-{original_id}"
    seen.add(code)
    return code


def main() -> None:
    inserted = updated = skipped = 0
    seen_codes: set[str] = set()

    with SessionLocal() as db:
        # Pre-load all existing active codes into the seen set to avoid re-using them
        # for synthetic codes. Real codes from the CSV still get deduped in order.
        for row in ITEMS_RAW:
            raw = row[1].strip()
            if raw:
                seen_codes.add(raw)   # reserve real barcodes before generating synthetics

        seen_codes.clear()  # reset — we resolve in-order below

        for original_id, raw_code, item_name in ITEMS_RAW:
            code = resolve_code(original_id, raw_code, seen_codes)
            category = detect_category(item_name)
            name = item_name.strip()

            existing = db.scalar(
                select(ItemMaster).where(
                    ItemMaster.item_code == code,
                    ItemMaster.deleted_at.is_(None),
                )
            )

            if existing:
                if existing.item_name != name or existing.category != category:
                    existing.item_name = name
                    if category:
                        existing.category = category
                    print(f"[update] {code} → {name} [{category}]")
                    updated += 1
                else:
                    print(f"[skip]   {code} — already up to date")
                    skipped += 1
            else:
                db.add(ItemMaster(
                    item_code=code,
                    item_name=name,
                    category=category,
                    is_active=True,
                ))
                print(f"[insert] {code} — {name} [{category}]")
                inserted += 1

        db.commit()

    print(f"\n✓ Done: {inserted} inserted, {updated} updated, {skipped} skipped.")


if __name__ == "__main__":
    main()
