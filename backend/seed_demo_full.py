"""Self-contained demo seed for the ONLINE demo (Postgres / server).

Creates the demo doctor + patients (they do not exist on a fresh deploy),
a schedule, appointments across the lifecycle, medical records, and a
published public profile. Idempotent: re-running rebuilds the demo set.

Run inside the backend container:
    cd /app && python manage.py shell < seed_demo_full.py
Anchored on 2026-06-03.
"""
import datetime as dt
from django.utils import timezone
from django.contrib.auth import get_user_model
from appointments.models import Appointment, DoctorScheduleSlot
from content.models import Department, DoctorProfile, DoctorDepartment

U = get_user_model()
TODAY = dt.date(2026, 6, 3)
PWD = "Demo@12345"

# --- doctor ---
doc, _ = U.objects.get_or_create(username="doctor_test", defaults={"role": "doctor"})
doc.role = "doctor"; doc.name = "Dr. Sarah Lin"; doc.email = "sarah.lin@example.com"
doc.set_password(PWD); doc.save()

# --- operator ---
op, _ = U.objects.get_or_create(username="ops_test", defaults={"role": "operator"})
op.role = "operator"; op.name = "Front Desk"; op.email = "ops@example.com"; op.phone = "13700000000"; op.set_password(PWD); op.save()

# --- patients ---
PATIENTS = [
    ("liam_chen", "Liam Chen"), ("olivia_wang", "Olivia Wang"),
    ("noah_li", "Noah Li"), ("emma_zhang", "Emma Zhang"),
    ("ethan_liu", "Ethan Liu"), ("sophia_yang", "Sophia Yang"),
    ("lucas_zhao", "Lucas Zhao"), ("mia_sun", "Mia Sun"),
]
pmap = {}
for uname, name in PATIENTS:
    u, _ = U.objects.get_or_create(username=uname, defaults={"role": "patient"})
    u.role = "patient"; u.name = name; u.email = f"{uname}@example.com"; u.set_password(PWD); u.save()
    pmap[uname] = u

# --- reset this doctor's appointments + slots ---
Appointment.objects.filter(doctor=doc).delete()
DoctorScheduleSlot.objects.filter(doctor=doc).delete()

TIMES = ["09:00", "09:30", "10:00", "10:30", "11:00", "14:00", "14:30", "15:00", "15:30", "16:00"]
booked = {(0, "09:00"), (0, "10:00"), (0, "14:30"), (1, "09:30"), (1, "11:00"),
          (1, "15:00"), (2, "10:30"), (3, "09:00")}
for d in range(4):
    day = TODAY + dt.timedelta(days=d)
    for t in TIMES:
        hh, mm = map(int, t.split(":"))
        DoctorScheduleSlot.objects.create(doctor=doc, slot_date=day, slot_time=dt.time(hh, mm),
                                          is_available=(d, t) not in booked)


def make(patient, d_off, t, reason, status, diag="", plan="", advice=""):
    hh, mm = map(int, t.split(":"))
    Appointment.objects.create(
        patient=pmap[patient], doctor=doc, appointment_date=TODAY + dt.timedelta(days=d_off),
        appointment_time=dt.time(hh, mm), reason=reason, status=status,
        diagnosis_result=diag, treatment_plan=plan, medical_advice=advice,
        confirm_info=("Please arrive 10 minutes early." if status == "confirmed" else ""),
        created_by=pmap[patient])


make("liam_chen", -2, "09:30", "Persistent cough and mild fever for 4 days", "completed",
     "Acute upper respiratory tract infection (viral).",
     "Symptomatic care; oral hydration; paracetamol 500mg PRN for fever.",
     "Rest 3 days. Return if fever persists beyond 72 hours or breathing worsens.")
make("emma_zhang", -2, "14:00", "Annual health check-up", "completed",
     "No acute findings. BP 122/78, BMI within normal range.",
     "Routine bloods ordered; lifestyle counselling provided.",
     "Maintain regular exercise; repeat lipid panel in 12 months.")
make("noah_li", -1, "10:00", "Follow-up on hypertension", "completed",
     "Essential hypertension, well controlled on current therapy.",
     "Continue amlodipine 5mg daily; home BP monitoring.",
     "Reduce salt intake; follow up in 8 weeks with BP diary.")
make("sophia_yang", -1, "15:30", "Lower back pain after lifting", "completed",
     "Mechanical lower back strain; no red-flag features.",
     "NSAIDs short course; physiotherapy referral.",
     "Avoid heavy lifting for 2 weeks; gentle stretching daily.")
make("olivia_wang", 0, "11:00", "Migraine with occasional dizziness", "confirmed")
make("ethan_liu", 0, "15:00", "Routine diabetes review (HbA1c)", "confirmed")
make("mia_sun", 0, "16:00", "New patient — persistent fatigue, requesting consultation", "pending")
make("mia_sun", 1, "10:00", "Skin rash on forearm, mildly itchy", "confirmed")
make("lucas_zhao", 1, "14:30", "Sore throat and hoarseness", "pending")
make("liam_chen", 2, "09:30", "Follow-up: cough review", "pending")
make("emma_zhang", 3, "11:00", "Recurrent headaches in the evening", "pending")
make("noah_li", 2, "16:00", "Knee pain — patient rescheduled", "cancelled")

# --- content: department + published public profile ---
dep, _ = Department.objects.get_or_create(slug="internal-medicine", defaults={"name": "Internal Medicine"})
dep.name = "Internal Medicine"
dep.summary = "Comprehensive adult primary and internal care — prevention, diagnosis, and chronic disease management."
dep.description_html = "<p>Our Internal Medicine department provides evidence-based care for adults, from routine check-ups to the long-term management of hypertension, diabetes, and respiratory conditions.</p>"
dep.is_published = True; dep.display_order = 1; dep.save()

bio = ("<p><strong>Dr. Sarah Lin</strong> is a board-certified internal medicine physician with over 12 years of "
       "clinical experience. She focuses on preventive care, hypertension, and diabetes management, and is known "
       "for clear, patient-centred communication.</p>"
       "<p>She completed her residency at the University Medical Center and has a special interest in chronic "
       "disease management and early health screening.</p>"
       "<ul><li>Hypertension &amp; cardiovascular risk</li><li>Diabetes &amp; metabolic health</li>"
       "<li>Preventive health check-ups</li></ul>")
prof, _ = DoctorProfile.objects.get_or_create(user=doc)
prof.title = "Senior Consultant Physician"; prof.specialty = "Internal Medicine"
prof.bio_published_html = bio; prof.bio_draft_html = bio
prof.is_published = True; prof.draft_status = DoctorProfile.DraftStatus.APPROVED
prof.draft_submitted_at = timezone.now(); prof.draft_reviewed_at = timezone.now()
prof.display_order = 1; prof.save()
DoctorDepartment.objects.get_or_create(doctor=prof, department=dep, defaults={"is_primary": True})

from collections import Counter
print("doctor:", doc.username, "id=", doc.id, "name=", doc.name)
print("operator:", op.username, "id=", op.id, "name=", op.name)
print("patients:", U.objects.filter(role="patient").count())
print("slots:", DoctorScheduleSlot.objects.filter(doctor=doc).count())
print("appointments:", dict(Counter(Appointment.objects.filter(doctor=doc).values_list("status", flat=True))))
print("profile published:", prof.is_published, "dept:", dep.name)
