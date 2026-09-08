"""Seed 40 test complaint rows from the dashboard snapshot.

Run from the api/ directory:
    python scripts/seed_complaints.py

Behaviour:
  - Rows whose comp_no already exists are SKIPPED.
  - Duplicate comp_no values in source get a _2 / _3 suffix.
  - "Under Proccess" (typo) is normalised to "Under Process".
  - Each row's last action is written to ComplaintStatusLog.
"""
import sys, os
from datetime import date, timezone, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import SessionLocal
from app.models.complaint import Complaint, ComplaintStatusLog

# ---------------------------------------------------------------------------
# Source data
# Columns:
#   comp_no | date (YYYY-MM-DD) | customer_name | status | query_type |
#   remark | mobile | model_details | problem_description |
#   email | address | source | action_taken
# ---------------------------------------------------------------------------
SEED_ROWS = [
    ("IDC_1780143424","2026-05-30","Anurag Agarwal","Pending","Sales","Gst No: 05ABKCS8377E1ZY","9997099345",None,"Gem's Partner","anurag.agarwal@sonestaanodic.com","Uttaranchal, 249408","public","Ask for Invoice"),
    ("IDC_1780133588","2026-05-30","Shivangi Dixit","In Process","Sales","dialed twice she is disconnect the call","9076737383",None,"REQUIREMENT OF AC THROUGH GEM",None,None,"callcenter","Ask for Invoice"),
    ("IDC_1780133081","2026-05-30","Bhabajit Barukh","Rejected","Sales","He has been working on GeM for the last three years with a turnover of Rs 3.5 crore","7002128252",None,"Require AC from GEM",None,None,"callcenter","Ask for Invoice"),
    ("IDC_1780131345","2026-05-30","Madan Gupta","In Process","Sales","he is not interested in onboarding process","9891799951",None,"Gem's Partner","quickservices9@gmail.com","Delhi, 110058","public","Ask for Invoice"),
    ("IDC_1780130548","2026-05-30","Harsh raj","Pending","Installation",None,"9556664602",None,"He want ac installation","harshraj82490@gmail.com","Near railway station bari pada construction dept","callcenter","Request Sent"),
    ("IDC_1780125667","2026-05-30","yogen singh","Pending","Installation",None,"9454404464","IDCACSBF16K5","customer wants to get ac install kindly coordinate","viruthakur5685@gmail.com","police station grp lalit pur","callcenter","Request Sent"),
    ("IDC_1780125009","2026-05-30","Rohit Rawat","In Process","Sales","I am not applying for this","8802626551",None,"Gem's Partner","rohitrawat03@gmail.com","Delhi, 110076","public","Ask for Invoice"),
    ("IDC_1780124373","2026-05-30","NA","Pending","Others",None,"8770647018",None,"COMPLAINT STATUS",None,None,"callcenter","Ask for Invoice"),
    ("IDC_1780124121","2026-05-30","NA","Pending","Others",None,"9460538481",None,"ABAND CALL BACK - COMPLAINT STATUS",None,None,"callcenter","Ask for Invoice"),
    ("IDC_1780122395","2026-05-30","PANKHURI","In Process","Sales","dialed twice she is not responding call","7488739026",None,"3 STAR AC WANTS TO PURCHASE IT",None,None,"callcenter","Ask for Invoice"),
    ("IDC_1780119880","2026-05-30","na","Pending","Others",None,"9136321577",None,"no response",None,None,"callcenter","Ask for Invoice"),
    ("IDC_1780118268","2026-05-30","bank of india","Pending","Installation",None,"8140014069","1.3tan split ac","installation request","pethapur.gandhinagar@bankofindia.bank.in","bank of india pethapur branch gandhi nagar 382610","callcenter","Ask for Invoice"),
    ("IDC_1780118268","2026-05-30","bank of india","Pending","Installation",None,"8140014069","1.3tan split ac","installation request","pethapur.gandhinagar@bankofindia.bank.in","bank of india pethapur branch gandhi nagar 382610","callcenter","Request Sent"),
    ("IDC_1780117879","2026-05-30","dr. davi dekka","Pending","Service",None,"9883365047","1tan split ac","ac not working","drdavidekka@gmail.com","Chhoto Salkumar SAD, Falakata RH, ALIPURDUAR, West Bengal","callcenter","Request Sent"),
    ("IDC_1780117714","2026-05-30","Dr. Devid Ekka","Pending","Installation",None,"9883365047","1tan split ac","installation requset","drdavidekka@gmail.com","Chhoto Salkumar SAD, Falakata RH, ALIPURDUAR, West Bengal","callcenter","Request Sent"),
    ("IDC_1780115147","2026-05-30","BIPIN RAUL","Pending","Service",None,"9004693689","1.5 TONN SPLIT","3 AC NOT WORKING","aecstar1office@yahoo.com","Anushree colony post tapp taluka and dist palghar boissar west 401504","callcenter","Request Sent"),
    ("IDC_1780109759","2026-05-30","NARENDRA MEENA","In Process","Sales","he is said amount bahut jada hai aap mail kar digiye","9982630333",None,"Gem's Partner","ecoonelife23@gmail.com","Rajasthan, 304024","public","Ask for Invoice"),
    ("IDC_1780067955","2026-05-29","NA","Pending","Others",None,"8750495439",None,"call back not connected","ABC@gmail.com","NA","callcenter","Ask for Invoice"),
    ("IDC_1780060847","2026-05-29","SOM PARKASH JANGRA","Pending","Service",None,"9467990900","Air Conditioner","Air Conditioner Not Cooling","somparkashjangra@gmail.com","BSF Institute of Communication and Information Technology New Delhi","public","Documents Received"),
    ("IDC_1780054427","2026-05-29","GOATAM KUMAR TIWARI","Pending","Service",None,"9643695009","1.5 TONN SPLIT","AC IS NOT COOLING PLEASE RESOLVE THIS ISSUE ASAP","srgraphicssrgraphics@gmail.com","D 165 SEC 10 NOIDA","callcenter","Request Sent"),
    ("IDC_1780050188","2026-05-29","Vijay","In Process","Sales","he is not interested in onboarding","8376953939",None,"Need 1 cassett ac and gem Authorization",None,None,"callcenter","Ask for Invoice"),
    ("IDC_1780045065","2026-05-29","SARASWATI RANA","In Process","Sales","Refrigerators ki requirements hai but abhi only code chaiye","9033410157",None,"Require OEM code",None,None,"callcenter","Ask for Invoice"),
    ("IDC_1780038639","2026-05-29","UDAY PRATAP SINGH","Pending","Others",None,"7451082575","2 TONN","NOT WORKING",None,None,"callcenter","Ask for Invoice"),
    ("IDC_1780038361","2026-05-29","CHANDRA RATAN","Pending","Service",None,"9602634130","2 TONN SPLIT","AC DISPLAY IS SHOWING F1 ERROR","dharmendrameena@powergrid.in","POWER GRID SUB STATION DABODA KHURD 124507","callcenter","Documents Received"),
    ("IDC_1780038500","2026-05-29","J GANAPATI","Pending","Service",None,"9471340782","Air Conditioner","AC machine power not ON.","jganapati37@gmail.com","220kv dvc dhanbad sub station, kandra industrial area dhanbad","public","Documents Received"),
    ("IDC_1780038074","2026-05-29","NA","Pending","Others",None,"9602634130",None,"CALL DROP",None,None,"callcenter","Ask for Invoice"),
    ("IDC_1780036583","2026-05-29","Randhir Kumar","Pending","Service",None,"9608120207","Air Conditioner","ODU PCB not working","randhir.kumar2@esic.gov.in","Bari BRahmna","public","Documents Received"),
    ("IDC_1780035565","2026-05-29","siva p pramood","In Process","Service","LOCAL TEAM VISIT THE SITE 1/6/2026","9567296404","IDCACESO23030600050","customer is saying that ac is not working kindly coordinate","sivapramodm@gmail.com","chander gorund water wall kasa asapuram","callcenter","Documents Received"),
    ("IDC_1780034621","2026-05-29","chander shaikher singh","Pending","Service",None,"8332997192","IDCACS24K5ING_2024","customer is saying that ac is not working kindly look into it","singh_chandrasekhar@ongc.co.in","ongc raj complex raja madaly anderpradesh 533106","callcenter","Request Sent"),
    ("IDC_1780034320","2026-05-29","Deepak Kumar","In Process","Sales","he is not interested in onboarding process","9957770910",None,"70 P AC through GEM",None,None,"callcenter","Ask for Invoice"),
    ("IDC_1780033497","2026-05-29","Amdx vigilance technologies","Under Process","Sales","he is interested he said i let you know","6386766743",None,"Require AC through GEM",None,None,"callcenter","Ask for Invoice"),
    ("IDC_1780033307","2026-05-29","NA","Pending","Others",None,"9760791100",None,"COMPLAINT STATUS",None,None,"callcenter","Ask for Invoice"),
    ("IDC_1780030561","2026-05-29","NA","Pending","Others",None,"7518202724",None,"COMPLAINT STATUS",None,None,"callcenter","Ask for Invoice"),
    ("IDC_1780030413","2026-05-29","-","Pending","Others",None,"9869720579",None,"WRONG NUMBER",None,None,"callcenter","Ask for Invoice"),
    ("IDC_1780027374","2026-05-29","HARSHIT KHNADELWAL","Pending","Service",None,"8619971540","1.5 TONN SPLIT AC","CF ERROR OCCUR","harshitk@cpri.in","PLOT NO. 3A INSTITUTIONAL AREA SECTOR - 62 NOIDA","callcenter","Request Sent"),
    ("IDC_1779969489","2026-05-28","gurpreet singh","Pending","Service",None,"8146110028","1 ton 2 ac","1 ton 2 ac service","misefaz@gmail.com",None,"callcenter","Ask for Invoice"),
    ("IDC_1779969489","2026-05-28","gurpreet singh","Pending","Service",None,"8146110028","1 ton 2 ac","1 ton 2 ac service","misefaz@gmail.com",None,"callcenter","Request Sent"),
    ("IDC_1779963445","2026-05-28","Preeti Gaur","In Process","Sales","process explain kar diya hai bol rahe hai hamara startup hai apka onboarding amount bahut jada hai","9058302387",None,"Gem's Partner","info@dealzonetraders.in","Uttaranchal, 246149","public","Ask for Invoice"),
    ("IDC_1779962346","2026-05-28","Himanshu","In Process","Sales","Gem ka process inko explain kar diya hai bol rahe hai mujhe direct chaiye mean as retail","7754881385",None,"Requirement of 45 units through GEM water cooler",None,None,"callcenter","Ask for Invoice"),
    ("IDC_1779961825","2026-05-28","Partha Pratim Majee","In Process","Service","LOCAL TEAM VISIT THE SITE 1/6/2026","9771448365","Air Conditioner","not cooling","sseelrnc@gmail.com","SSE/EL/G/RNC near Ranchi railway station","public","Documents Received"),
    ("IDC_1780200001","2026-06-01","Kavita Sharma","Pending","Installation",None,"9811122233","Split AC IDCACS24K5","Customer requested installation scheduling","kavita.sharma@example.com","Sector 15, Gurgaon, Haryana","callcenter","Request Sent"),
    ("IDC_1780200002","2026-06-01","Mohit Verma","In Process","Service",None,"9811122234","Window AC IDCACW18K3","AC remote not working","mohit.verma@example.com","Ashok Vihar, Delhi","callcenter","Documents Received"),
    ("IDC_1780200003","2026-06-02","Asha Gupta","Pending","Sales",None,"9811122235",None,"Wants quotation for geyser bulk order","asha.gupta@example.com","Bhopal, Madhya Pradesh","public","Ask for Invoice"),
    ("IDC_1780200004","2026-06-02","Rakesh Thakur","Pending","Installation",None,"9811122236","Geyser IDCWH35L","Need engineer visit for water heater placement","rakesh.thakur@example.com","Shimla, Himachal Pradesh","callcenter","Request Sent"),
    ("IDC_1780200005","2026-06-03","Nisha Jain","In Process","Service",None,"9811122237","Fridge IDCFRD360L","Compressor noise issue reported","nisha.jain@example.com","Panchkula, Haryana","callcenter","Request Sent"),
    ("IDC_1780200006","2026-06-03","Harish Mehra","Pending","Service",None,"9811122238","Split AC IDCACS13K3E","Service request for cooling issue after power fluctuation","harish.mehra@example.com","Kota, Rajasthan","callcenter","Request Sent"),
    ("IDC_1780200007","2026-06-04","Sonal Kapoor","Pending","Installation",None,"9811122239","Window AC IDCACW24K3E","Need installation appointment for new unit","sonal.kapoor@example.com","Jodhpur, Rajasthan","callcenter","Request Sent"),
    ("IDC_1780200008","2026-06-04","Ritu Singh","In Process","Sales",None,"9811122240",None,"Interested in bulk air cooler purchase","ritu.singh@example.com","Raipur, Chhattisgarh","public","Ask for Invoice"),
]

STATUS_MAP = {
    "Under Proccess": "Under Process",   # normalise common typo
    "Under Process":  "Under Process",
}

VALID_ACTIONS = {"Ask for Invoice", "Request Sent", "Documents Received"}


def resolve_status(s: str) -> str:
    return STATUS_MAP.get(s, s)


def main() -> None:
    inserted = skipped = 0

    with SessionLocal() as db:
        # Pre-load existing comp_no values
        existing = {c for c in db.scalars(select(Complaint.comp_no)).all()}
        # Track comp_nos used in this run (for deduplication)
        used: dict[str, int] = {}

        for row in SEED_ROWS:
            (comp_no, date_str, customer_name, status_raw, query_type,
             remark, mobile, model_details, problem_description,
             email, address, source, action_taken) = row

            status = resolve_status(status_raw)

            # Deduplicate comp_no
            base = comp_no
            if base in used:
                used[base] += 1
                comp_no = f"{base}_{used[base]}"
            else:
                used[base] = 1

            if comp_no in existing:
                print(f"[skip]   {comp_no} — already exists")
                skipped += 1
                continue

            comp_date = date.fromisoformat(date_str)

            c = Complaint(
                comp_no=comp_no,
                comp_date=comp_date,
                customer_name=customer_name,
                customer_mobile=mobile,
                customer_email=email if email and email not in ("—", "NA", "na") else None,
                customer_address=address if address and address not in ("—", "NA", "na") else None,
                model_details=model_details if model_details and model_details not in ("—", "N/A") else None,
                problem_description=problem_description if problem_description and problem_description not in ("—",) else None,
                query_type=query_type,
                remark=remark if remark and remark not in ("—", "N/A") else None,
                status=status,
                access_code="000000",
                send_sms=False,
                source=source,
                status_date=datetime.now(timezone.utc),
            )
            db.add(c)
            db.flush()

            # Initial creation log
            db.add(ComplaintStatusLog(
                complaint_id=c.id,
                old_status=None,
                new_status=status,
                remark="Seeded test data",
            ))

            # Action log
            if action_taken and action_taken in VALID_ACTIONS:
                db.add(ComplaintStatusLog(
                    complaint_id=c.id,
                    old_status=status,
                    new_status=status,
                    action_taken=action_taken,
                    remark=f"Seeded: {action_taken}",
                ))

            existing.add(comp_no)
            print(f"[insert] {comp_no} — {customer_name} ({status}) / {query_type}")
            inserted += 1

        db.commit()

    print(f"\n✓ Done: {inserted} inserted, {skipped} skipped.")


if __name__ == "__main__":
    main()
