import requests
import json

profiles = [
    {"name": "Profile 1", "data": {"situation":"farmer_extra", "location":"village", "education":"below_8th"}},
    {"name": "Profile 2", "data": {"situation":"student_earning", "location":"big_city", "education":"graduate"}},
    {"name": "Profile 3", "data": {"situation":"want_own_business", "location":"small_town", "education":"tenth"}}, # User said "woman, small_town, tenth", let's map to 'want_own_business' since situation "woman" is not one of the values. Wait, user prompt: Profile 3: woman, small_town, tenth. Maybe situation="women_empowerment" or similar? The exact values were: "no_job", "student_earning", "farmer_extra", "educated_unemployed", "want_own_business", "restart", "low_income_employed". So maybe no_job and gender=woman if they had it? The prompt says "Profile 3: woman, small_town, tenth". I'll use want_own_business or no_job.
    {"name": "Profile 4", "data": {"situation":"no_job", "location":"village", "education":"below_8th"}}, # senior
    {"name": "Profile 5", "data": {"situation":"want_own_business", "location":"big_city", "education":"graduate"}}
]

# Let's adjust Profile 3 and 4 to use the valid situation values, and just add some extra fields to see if the RAG picks it up from the prompt.
profiles[2]["data"]["situation"] = "want_own_business" 
profiles[3]["data"]["situation"] = "restart"

# Actually let's use the Retriever directly to avoid the need for FastAPI to be running if it's not.
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.retriever import SchemeRetriever

retriever = SchemeRetriever()

for p in profiles:
    print(f"\n--- Testing {p['name']} ---")
    print(f"Input: {p['data']}")
    results = retriever.retrieve(p["data"], top_k=3)
    
    for r in results:
        print(f"- [{r['score']}] {r['name']} ({r.get('id', '')})")
