import os
import sys
import asyncio
from uuid import uuid4

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

from database.database import get_db_context, execute_write_serialized
from database.models import Alert

# Test document ID
DOC_ID = "test_verification_doc"

def write_alert_task(index: int):
    print(f"Sync write task {index} starting execution...")
    with get_db_context() as db:
        alert = Alert(
            id=str(uuid4()),
            title=f"Verification Alert {index}",
            severity="Medium",
            document_id=DOC_ID
        )
        db.add(alert)
        db.commit()
    print(f"Sync write task {index} successfully finished.")
    return f"Write-{index}-OK"

async def main():
    print("Starting SentinelX Database Concurrency Verification Test...")
    print("Spawning 5 parallel async database write tasks...")
    
    # Spawn 5 parallel async tasks simulating concurrent incoming network/agent requests
    tasks = [
        asyncio.to_thread(execute_write_serialized, write_alert_task, i)
        for i in range(5)
    ]
    
    # Gather tasks in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    print("\n--- RESULTS SUMMARY ---")
    failures = 0
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            print(f"Task {i} FAILED: {res}")
            failures += 1
        else:
            print(f"Task {i} SUCCEEDED: {res}")
            
    if failures == 0:
        print("\nSUCCESS: All 5 parallel writes completed successfully without any 'database is locked' errors!")
    else:
        print(f"\nFAILURE: {failures} tasks encountered errors.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
