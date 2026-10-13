from app.db.session import SessionLocal
from app.services.diagnostic_service import generate_diagnostics


db = SessionLocal()

try:
    report = generate_diagnostics(db, analysis_id=13)

    from pprint import pprint
    pprint(report)

finally:
    db.close()