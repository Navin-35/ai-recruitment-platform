"""
Seed script to populate sample jobs and candidate profiles and run AI matching pipeline.
Run with: python seed_demo_data.py
"""

from pathlib import Path
from app.core.database import SessionLocal
from app.core.init_db import init_database
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.resume import Resume
from app.workflows.matching_pipeline import matching_pipeline

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"


def seed_data():
    init_database()
    db = SessionLocal()

    print("[INFO] Seeding AI Recruitment Platform with sample data...")

    # 1. Seed Senior Backend Job
    backend_jd_path = SAMPLES_DIR / "job_descriptions" / "senior_backend_engineer.txt"
    if backend_jd_path.exists():
        backend_jd_text = backend_jd_path.read_text(encoding="utf-8")
        job1 = (
            db.query(Job)
            .filter(Job.title == "Senior Backend Engineer")
            .first()
        )
        if not job1:
            job1 = Job(
                title="Senior Backend Engineer",
                company_name="CloudScale Systems",
                description=backend_jd_text,
                location="Remote",
            )
            db.add(job1)
            db.commit()
            db.refresh(job1)
            print(f"[OK] Created Job: {job1.title} (ID: {job1.id})")

            # Extract requirements & embed chunks
            print(f"[AI] Decomposing requirements for Job #{job1.id}...")
            matching_pipeline.process_and_index_job(job1.id, db)
            print(f"     Indexed {len(job1.requirements)} atomic requirements.")
    else:
        print("Backend JD file not found.")

    # 2. Seed Machine Learning Job
    ml_jd_path = SAMPLES_DIR / "job_descriptions" / "machine_learning_engineer.txt"
    if ml_jd_path.exists():
        ml_jd_text = ml_jd_path.read_text(encoding="utf-8")
        job2 = (
            db.query(Job)
            .filter(Job.title == "Machine Learning Engineer")
            .first()
        )
        if not job2:
            job2 = Job(
                title="Machine Learning Engineer",
                company_name="DeepMind Intelligence",
                description=ml_jd_text,
                location="San Francisco, CA",
            )
            db.add(job2)
            db.commit()
            db.refresh(job2)
            print(f"[OK] Created Job: {job2.title} (ID: {job2.id})")

            print(f"[AI] Decomposing requirements for Job #{job2.id}...")
            matching_pipeline.process_and_index_job(job2.id, db)
            print(f"     Indexed {len(job2.requirements)} atomic requirements.")

    # 3. Seed Candidates
    candidates_info = [
        ("John Smith", "john.smith@example.com", "john_smith_senior_backend.txt"),
        ("Elena Rostova", "elena.rostova@example.com", "elena_rostova_ml_specialist.txt"),
        ("Alex Rivera", "alex.rivera@example.com", "alex_junior_dev.txt"),
    ]

    for name, email, filename in candidates_info:
        resume_file = SAMPLES_DIR / "resumes" / filename
        if not resume_file.exists():
            continue

        raw_resume = resume_file.read_text(encoding="utf-8")
        cand = db.query(Candidate).filter(Candidate.email == email).first()
        if not cand:
            cand = Candidate(name=name, email=email)
            db.add(cand)
            db.commit()
            db.refresh(cand)

            resume = Resume(
                candidate_id=cand.id,
                filename=filename,
                file_type="txt",
                extracted_text=raw_resume,
                processing_status="pending",
            )
            db.add(resume)
            db.commit()
            db.refresh(resume)

            print(f"[AI] Processing & vector indexing resume for {name} (Candidate #{cand.id})...")
            matching_pipeline.process_and_index_resume(resume.id, db)
            print(f"     Successfully indexed {name}.")

    # 4. Run AI matching for Senior Backend Job
    if job1:
        print(f"\n[AI] Executing AI Matching Pipeline & Leaderboard for Job #{job1.id}...")
        ranking = matching_pipeline.rank_candidates_for_job(job1.id, db)
        print("\n--- LEADERBOARD ---")
        for r in ranking:
            print(
                f"Rank #{r['rank']} | Score: {r['final_score']:.1f}/100 | "
                f"Candidate: {r['candidate_name']} | Fit: {r['grounded_explanation']['overall_fit'].upper()}"
            )
            print(
                f"  Breakdown -> Skills: {r['score_breakdown']['required_skill_score']} | "
                f"Exp: {r['score_breakdown']['experience_score']} | "
                f"Projects: {r['score_breakdown']['project_score']} | "
                f"Edu: {r['score_breakdown']['education_score']}"
            )

    db.close()
    print("\n[OK] Database seeding and AI matching demo complete!")


if __name__ == "__main__":
    seed_data()
