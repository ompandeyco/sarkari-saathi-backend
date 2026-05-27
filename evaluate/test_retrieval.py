import os
import sys
import time
import json

# Add parent directory to path so we can import the rag module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.retriever import SchemeRetriever

TEST_CASES = [
    {
        "id": "TC001",
        "profile": {
            "situation": "no_job",
            "education": "tenth",
            "location": "village",
            "has_phone": "yes_basic",
            "target_earning": "5k_10k"
        },
        "must_include": ["MGNREGA", "PMKVY", "Kaushal"],
        "must_not_include": ["Stand Up India", "EWS Scholarship"],
        "reason": "Uneducated rural unemployed needing immediate wage or basic skill"
    },
    {
        "id": "TC002", 
        "profile": {
            "situation": "student_earning",
            "education": "graduate",
            "location": "urban",
            "has_phone": "yes_daily",
            "target_earning": "10k_25k"
        },
        "must_include": ["PMKVY", "Scholarship", "NSP"],
        "must_not_include": ["MGNREGA", "PM Kisan", "Janani Suraksha"],
        "reason": "Urban graduate student looking for skills/internships/scholarships"
    },
    {
        "id": "TC003", 
        "profile": {
            "situation": "farmer_extra",
            "education": "eighth",
            "location": "village",
            "has_phone": "yes_basic",
            "target_earning": "10k_25k"
        },
        "must_include": ["Kisan Samman", "PMFBY", "Kisan Credit"],
        "must_not_include": ["SVANidhi", "Ujjwala", "Education"],
        "reason": "Farmer needing agricultural subsidies and crop insurance"
    },
    {
        "id": "TC004", 
        "profile": {
            "situation": "business_idea",
            "education": "tenth",
            "location": "urban",
            "has_phone": "yes_daily",
            "target_earning": "25k_plus"
        },
        "must_include": ["SVANidhi", "Mudra"],
        "must_not_include": ["MGNREGA", "Kisan", "Soil Health"],
        "reason": "Urban street vendor or small business aspirant"
    },
    {
        "id": "TC005", 
        "profile": {
            "situation": "women_empowerment",
            "education": "none",
            "location": "village",
            "has_phone": "no",
            "target_earning": "under_5k"
        },
        "must_include": ["Ujjwala", "Matru Vandana", "NRLM", "Aajeevika"],
        "must_not_include": ["Stand Up India", "EWS Scholarship", "SVANidhi"],
        "reason": "BPL rural woman needing basic welfare and SHG support"
    },
    {
        "id": "TC006", 
        "profile": {
            "situation": "no_job",
            "education": "none",
            "location": "village",
            "has_phone": "no",
            "target_earning": "under_5k"
        },
        "must_include": ["Old Age Pension", "IGNOAPS"],
        "must_not_include": ["Scholarship", "Mudra", "Startup"],
        "reason": "Rural elderly needing pension (assumed via no_job/none ed/no phone proxy)"
    },
    {
        "id": "TC007", 
        "profile": {
            "situation": "women_empowerment",
            "education": "graduate",
            "location": "urban",
            "has_phone": "yes_daily",
            "target_earning": "25k_plus"
        },
        "must_include": ["Stand Up India", "Mudra"],
        "must_not_include": ["MGNREGA", "Ujjwala", "PM Awas Yojana - Gramin"],
        "reason": "Educated urban woman looking to start an enterprise"
    },
    {
        "id": "TC008", 
        "profile": {
            "situation": "no_job",
            "education": "eighth",
            "location": "village",
            "has_phone": "yes_basic",
            "target_earning": "under_5k"
        },
        "must_include": ["Awas Yojana", "PMAY", "Gramin"],
        "must_not_include": ["SVANidhi", "EWS Scholarship", "Education"],
        "reason": "Rural poor needing housing and basic survival"
    },
    {
        "id": "TC009", 
        "profile": {
            "situation": "student_earning",
            "education": "twelfth",
            "location": "urban",
            "has_phone": "yes_daily",
            "target_earning": "5k_10k"
        },
        "must_include": ["Sukanya", "Beti Bachao", "Scholarship"],
        "must_not_include": ["Kisan", "Farmer", "MGNREGA"],
        "reason": "Young student/girl child education focus"
    },
    {
        "id": "TC010", 
        "profile": {
            "situation": "business_idea",
            "education": "tenth",
            "location": "village",
            "has_phone": "yes_basic",
            "target_earning": "10k_25k"
        },
        "must_include": ["Vishwakarma", "Mudra", "Artisan"],
        "must_not_include": ["Education", "Scholarship", "Urban"],
        "reason": "Rural artisan or tradesperson"
    },
    {
        "id": "TC011", 
        "profile": {
            "situation": "no_job",
            "education": "none",
            "location": "urban",
            "has_phone": "yes_basic",
            "target_earning": "under_5k"
        },
        "must_include": ["Garib Kalyan", "Ration", "PMGKAY"],
        "must_not_include": ["Stand Up India", "Startup", "Agricultural"],
        "reason": "Urban extreme poor needing food security"
    },
    {
        "id": "TC012", 
        "profile": {
            "situation": "women_empowerment",
            "education": "tenth",
            "location": "village",
            "has_phone": "yes_daily",
            "target_earning": "5k_10k"
        },
        "must_include": ["NRLM", "SHG", "Aajeevika", "Mudra"],
        "must_not_include": ["Urban", "SVANidhi", "Student"],
        "reason": "Rural woman looking for SHG or micro-loans"
    },
    {
        "id": "TC013", 
        "profile": {
            "situation": "no_job",
            "education": "tenth",
            "location": "village",
            "has_phone": "yes_basic",
            "target_earning": "5k_10k"
        },
        "must_include": ["DDU-GKY", "Kaushalya", "Skill"],
        "must_not_include": ["Urban", "Business", "Startup"],
        "reason": "Rural youth needing skill placement"
    },
    {
        "id": "TC014", 
        "profile": {
            "situation": "women_empowerment",
            "education": "eighth",
            "location": "village",
            "has_phone": "no",
            "target_earning": "under_5k"
        },
        "must_include": ["Janani", "Suraksha", "Matru", "Pregnant"],
        "must_not_include": ["Startup", "Student", "Business"],
        "reason": "Rural pregnant woman maternity benefits"
    },
    {
        "id": "TC015", 
        "profile": {
            "situation": "student_earning",
            "education": "twelfth",
            "location": "urban",
            "has_phone": "yes_daily",
            "target_earning": "5k_10k"
        },
        "must_include": ["EWS", "Central Sector Scholarship", "Scholarship"],
        "must_not_include": ["Kisan", "MGNREGA", "Awas"],
        "reason": "EWS urban student needing scholarship"
    },
    {
        "id": "TC016", 
        "profile": {
            "situation": "farmer_extra",
            "education": "tenth",
            "location": "village",
            "has_phone": "yes_basic",
            "target_earning": "25k_plus"
        },
        "must_include": ["Kisan Credit Card", "KCC", "Loan"],
        "must_not_include": ["Student", "Urban", "SVANidhi"],
        "reason": "Farmer needing high credit line"
    },
    {
        "id": "TC017", 
        "profile": {
            "situation": "farmer_extra",
            "education": "none",
            "location": "village",
            "has_phone": "no",
            "target_earning": "under_5k"
        },
        "must_include": ["Soil Health Card", "Soil", "Health"],
        "must_not_include": ["Urban", "Business", "Education"],
        "reason": "Farmer needing soil testing"
    },
    {
        "id": "TC018", 
        "profile": {
            "situation": "no_job",
            "education": "tenth",
            "location": "urban",
            "has_phone": "yes_daily",
            "target_earning": "5k_10k"
        },
        "must_include": ["PMKVY", "Skill", "Kaushal"],
        "must_not_include": ["MGNREGA", "Farmer", "Kisan"],
        "reason": "Urban youth needing skills"
    },
    {
        "id": "TC019", 
        "profile": {
            "situation": "business_idea",
            "education": "graduate",
            "location": "urban",
            "has_phone": "yes_daily",
            "target_earning": "25k_plus"
        },
        "must_include": ["Stand Up India", "Mudra", "Loan"],
        "must_not_include": ["MGNREGA", "Farmer", "BPL"],
        "reason": "Educated urban aspirant for big loans"
    },
    {
        "id": "TC020", 
        "profile": {
            "situation": "no_job",
            "education": "none",
            "location": "urban",
            "has_phone": "no",
            "target_earning": "under_5k"
        },
        "must_include": ["Disability", "Pension", "IGNDPS", "Garib"],
        "must_not_include": ["Startup", "Student", "Scholarship"],
        "reason": "Vulnerable urban poor needing pension/food"
    }
]

def check_match(scheme_text, keywords):
    text = scheme_text.lower()
    return any(kw.lower() in text for kw in keywords)

def evaluate_system():
    print("Initializing Retriever...")
    retriever = SchemeRetriever()
    
    total_cases = len(TEST_CASES)
    total_precision_5 = 0.0
    total_recall_10 = 0.0
    total_mrr = 0.0
    total_neg_precision = 0.0
    
    latencies = {}
    
    for i, tc in enumerate(TEST_CASES):
        profile = tc['profile']
        must_inc = tc['must_include']
        must_not = tc['must_not_include']
        
        start_time = time.time()
        # Fetch top 10 to calculate Recall@10
        results = retriever.retrieve(profile, top_k=10)
        latency_ms = int((time.time() - start_time) * 1000)
        latencies[tc['id']] = latency_ms
        
        # We need a unified string for each result to check against keywords
        result_texts = [f"{r['name']} {r['benefit']} {r['eligibility']}" for r in results]
        
        # Calculate Precision@5 (Top 5 results only)
        top_5_texts = result_texts[:5]
        hits_in_top_5 = 0
        for text in top_5_texts:
            if check_match(text, must_inc):
                hits_in_top_5 += 1
        
        # To avoid penalizing if there are fewer than 5 valid schemes in the DB,
        # we calculate precision as hits / min(5, len(must_include)).
        max_possible_hits = min(5, len(must_inc))
        precision_5 = hits_in_top_5 / max_possible_hits if max_possible_hits > 0 else 1.0
        # Cap at 1.0
        precision_5 = min(1.0, precision_5)
        total_precision_5 += precision_5
        
        # Calculate Recall@10
        hits_in_top_10 = sum(1 for text in result_texts if check_match(text, must_inc))
        max_possible_recall = len(must_inc)
        recall_10 = hits_in_top_10 / max_possible_recall if max_possible_recall > 0 else 1.0
        recall_10 = min(1.0, recall_10)
        total_recall_10 += recall_10
        
        # Calculate MRR (Mean Reciprocal Rank)
        mrr = 0.0
        for rank, text in enumerate(result_texts, 1):
            if check_match(text, must_inc):
                mrr = 1.0 / rank
                break
        total_mrr += mrr
        
        # Calculate Negative Precision (How many must_nots were correctly excluded from Top 10)
        neg_violations = sum(1 for text in result_texts if check_match(text, must_not))
        neg_precision = 1.0 - (neg_violations / len(result_texts)) if len(result_texts) > 0 else 1.0
        total_neg_precision += neg_precision
        
    # Aggregate Metrics
    avg_precision = (total_precision_5 / total_cases) * 100
    avg_recall = (total_recall_10 / total_cases) * 100
    avg_mrr = total_mrr / total_cases
    avg_neg_prec = (total_neg_precision / total_cases) * 100
    
    # Latency Metrics
    slowest_tc = max(latencies, key=latencies.get)
    fastest_tc = min(latencies, key=latencies.get)
    avg_latency = sum(latencies.values()) / len(latencies)
    
    # Determine Grade
    if avg_precision >= 85:
        grade = "A"
    elif avg_precision >= 70:
        grade = "B"
    elif avg_precision >= 50:
        grade = "C"
    else:
        grade = "D"

    # Build Report
    report = f"""=== RAG Evaluation Report ===
Total test cases: {total_cases}
Precision@5:  {avg_precision:.1f}%
Recall@10:    {avg_recall:.1f}%
MRR:          {avg_mrr:.2f}
Neg Precision: {avg_neg_prec:.1f}%

Slowest query: {slowest_tc} ({latencies[slowest_tc]}ms)
Fastest query: {fastest_tc} ({latencies[fastest_tc]}ms)
Average latency: {avg_latency:.0f}ms

Grade: {grade} (>85% precision)
"""
    
    print("\n" + report)
    
    # Save JSON Results
    results_data = {
        "metrics": {
            "total_test_cases": total_cases,
            "precision_at_5": round(avg_precision, 1),
            "recall_at_10": round(avg_recall, 1),
            "mrr": round(avg_mrr, 2),
            "negative_precision": round(avg_neg_prec, 1)
        },
        "performance": {
            "slowest_query_id": slowest_tc,
            "slowest_latency_ms": latencies[slowest_tc],
            "fastest_query_id": fastest_tc,
            "fastest_latency_ms": latencies[fastest_tc],
            "average_latency_ms": round(avg_latency)
        },
        "grade": grade,
        "timestamp": time.time()
    }
    
    results_path = os.path.join(os.path.dirname(__file__), "results.json")
    with open(results_path, "w") as f:
        json.dump(results_data, f, indent=2)
        
    print(f"Saved detailed results to {results_path}")

if __name__ == "__main__":
    evaluate_system()
