import subprocess
import time
import requests
import json
import sys

def main():
    print("--- Starting Backend Integration Tests ---\n")
    
    # Start the server
    print("Step 1: Starting Uvicorn server...")
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    print("Waiting for server to load models... (10s)")
    time.sleep(10)
    
    try:
        # Step 2: Health endpoint
        print("\nStep 2: Testing /health endpoint...")
        resp = requests.get("http://localhost:8000/health")
        if resp.status_code == 200:
            print("  PASS - Status 200")
            print(f"  Response: {resp.json()}")
        else:
            print(f"  FAIL - Status {resp.status_code}")
            
        # Step 3: Match schemes (Hindi)
        print("\nStep 3: Testing /match-schemes (Hindi/No Job)...")
        payload_hi = {
            "profile": {
                "situation": "no_job",
                "education": "tenth",
                "location": "village",
                "has_phone": True,
                "target_earning": "5k_10k"
            },
            "lang": "hi"
        }
        resp_hi = requests.post("http://localhost:8000/match-schemes", json=payload_hi)
        if resp_hi.status_code == 200:
            print("  PASS - Status 200")
            data = resp_hi.json()
            schemes = data.get("schemes", [])
            print(f"  Returned {len(schemes)} schemes.")
            if schemes:
                print(f"  Top Scheme: {schemes[0].get('name_hi', schemes[0].get('name', 'Unknown'))}")
        else:
            print(f"  FAIL - Status {resp_hi.status_code}")
            print(f"  Error: {resp_hi.text}")
            
        # Step 4: Match schemes (English)
        print("\nStep 4: Testing /match-schemes (English/Student)...")
        payload_en = {
            "profile": {
                "situation": "student_earning", 
                "education": "graduate",
                "location": "big_city",
                "has_phone": True,
                "target_earning": "10k_25k"
            },
            "lang": "en"
        }
        resp_en = requests.post("http://localhost:8000/match-schemes", json=payload_en)
        if resp_en.status_code == 200:
            print("  PASS - Status 200")
            data = resp_en.json()
            schemes = data.get("schemes", [])
            print(f"  Returned {len(schemes)} schemes.")
            if schemes:
                print(f"  Top Scheme: {schemes[0].get('name_en', schemes[0].get('name', 'Unknown'))}")
        else:
            print(f"  FAIL - Status {resp_en.status_code}")
            print(f"  Error: {resp_en.text}")
            
    finally:
        print("\nShutting down server...")
        server.terminate()
        server.wait()
        print("Integration tests complete.")

if __name__ == "__main__":
    main()
