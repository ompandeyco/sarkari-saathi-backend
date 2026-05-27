import os
import re
import json
import requests
from bs4 import BeautifulSoup

API_URL = "https://api.myscheme.gov.in/search/v4/schemes"
BATCH_SIZE = 150

def clean_html(raw_html):
    """Remove HTML tags and extra whitespaces from text."""
    if not raw_html:
        return ""
    soup = BeautifulSoup(str(raw_html), "html.parser")
    text = soup.get_text(separator=" ")
    return re.sub(r'\s+', ' ', text).strip()

def extract_tags(text):
    """Extract tags based on text."""
    text_lower = text.lower()
    tags = []
    if "farmer" in text_lower or "agriculture" in text_lower or "kisan" in text_lower or "crop" in text_lower:
        tags.append("farmer")
    if "student" in text_lower or "scholarship" in text_lower or "education" in text_lower or "school" in text_lower:
        tags.append("student")
    if "women" in text_lower or "girl" in text_lower or "mahila" in text_lower or "maternity" in text_lower or "widow" in text_lower:
        tags.append("women")
    if "health" in text_lower or "medical" in text_lower or "disease" in text_lower or "ayushman" in text_lower or "hospital" in text_lower:
        tags.append("health")
        
    if not tags:
        tags.append("other")
        
    return list(set(tags))

def get_hardcoded_schemes():
    """Fallback hardcoded list of 50 important schemes."""
    # List of 50 schemes spanning various categories
    base_schemes = [
        # Farmer (10)
        ("PM-Kisan Samman Nidhi", "पीएम-किसान सम्मान निधि", "Rs. 6000 per year income support", "Small and marginal farmers", "farmer", "MoA&FW"),
        ("PM Fasal Bima Yojana", "पीएम फसल बीमा योजना", "Crop insurance cover against natural calamities", "Farmers growing notified crops", "farmer", "MoA&FW"),
        ("Kisan Credit Card (KCC)", "किसान क्रेडिट कार्ड", "Short-term credit for farming needs", "All farmers", "farmer", "MoA&FW"),
        ("Soil Health Card Scheme", "मृदा स्वास्थ्य कार्ड", "Information on soil nutrient status", "All farmers", "farmer", "MoA&FW"),
        ("PM Krishi Sinchayee Yojana", "पीएम कृषि सिंचाई योजना", "Irrigation facilities and water conservation", "Farmers", "farmer", "MoA&FW"),
        ("National Agriculture Market (eNAM)", "राष्ट्रीय कृषि बाजार", "Online trading platform for agricultural commodities", "Farmers, traders", "farmer", "MoA&FW"),
        ("Paramparagat Krishi Vikas Yojana", "परम्परागत कृषि विकास योजना", "Promotion of organic farming", "Farmers", "farmer", "MoA&FW"),
        ("Gramin Bhandaran Yojana", "ग्रामीण भंडारण योजना", "Subsidy for construction of godowns", "Farmers, NGOs", "farmer", "MoA&FW"),
        ("Livestock Insurance Scheme", "पशुधन बीमा योजना", "Insurance cover for livestock", "Farmers, cattle rearers", "farmer", "MoA&FW"),
        ("PM Kisan Maan Dhan Yojana", "पीएम किसान मान धन योजना", "Rs. 3000/month pension", "Small and marginal farmers aged 18-40", "farmer,pension", "MoA&FW"),
        
        # Student (10)
        ("Post Matric Scholarship for Minorities", "अल्पसंख्यकों के लिए पोस्ट मैट्रिक छात्रवृत्ति", "Financial assistance for education", "Minority students Class 11 to Ph.D", "student", "MoMA"),
        ("Pre Matric Scholarship for Minorities", "अल्पसंख्यकों के लिए प्री मैट्रिक छात्रवृत्ति", "Financial assistance for education", "Minority students Class 1 to 10", "student", "MoMA"),
        ("National Means-cum-Merit Scholarship", "राष्ट्रीय साधन-सह-योग्यता छात्रवृत्ति", "Rs. 12000 per annum", "Students studying in class IX", "student", "MoE"),
        ("Central Sector Scheme of Scholarships", "केंद्रीय क्षेत्र छात्रवृत्ति योजना", "Financial assistance", "University/College students above 80th percentile", "student", "MoE"),
        ("Begum Hazrat Mahal National Scholarship", "बेगम हजरत महल राष्ट्रीय छात्रवृत्ति", "Scholarship for meritorious girls", "Minority girl students Class 9 to 12", "student,women", "MoMA"),
        ("PM Research Fellowship (PMRF)", "पीएम रिसर्च फेलोशिप", "Fellowship for research", "B.Tech/M.Sc/M.Tech students", "student", "MoE"),
        ("Pragati Scholarship", "प्रगति छात्रवृत्ति", "Rs. 50,000 per annum", "Girl students taking admission in AICTE approved institution", "student,women", "MoE"),
        ("Saksham Scholarship", "सक्षम छात्रवृत्ति", "Rs. 50,000 per annum", "Specially-abled students", "student", "MoE"),
        ("Ishan Uday Special Scholarship", "ईशान उदय विशेष छात्रवृत्ति", "Scholarship for NER students", "Students from North Eastern Region", "student", "UGC"),
        ("Swami Vivekananda Merit Cum Means Scholarship", "स्वामी विवेकानंद छात्रवृत्ति", "Financial assistance", "Meritorious students of West Bengal", "student", "State"),
        
        # Women (10)
        ("Pradhan Mantri Matru Vandana Yojana", "प्रधानमंत्री मातृ वंदना योजना", "Rs. 5000 cash incentive", "Pregnant women and lactating mothers", "women,health", "MoWCD"),
        ("Beti Bachao Beti Padhao", "बेटी बचाओ बेटी पढ़ाओ", "Awareness and welfare of girl child", "Girl child", "women,student", "MoWCD"),
        ("Sukanya Samriddhi Yojana", "सुकन्या समृद्धि योजना", "High interest savings scheme", "Girl child below 10 years", "women", "MoF"),
        ("Mahila Shakti Kendra", "महिला शक्ति केंद्र", "Empowerment of rural women", "Rural women", "women", "MoWCD"),
        ("Stand-Up India Scheme", "स्टैंड अप इंडिया", "Bank loans between 10 lakh and 1 crore", "SC/ST and/or women entrepreneurs", "women,other", "MoF"),
        ("Ujjwala Yojana", "उज्ज्वला योजना", "Free LPG connection", "Women of BPL families", "women,other", "MoPNG"),
        ("Working Women Hostel", "कामकाजी महिला छात्रावास", "Safe accommodation", "Working women", "women", "MoWCD"),
        ("One Stop Centre Scheme", "वन स्टॉप सेंटर", "Support for women affected by violence", "Women facing physical, psychological violence", "women", "MoWCD"),
        ("STEP Scheme", "स्टेप योजना", "Skill training for employment", "Women aged 16 and above", "women", "MoWCD"),
        ("Nari Shakti Puraskar", "नारी शक्ति पुरस्कार", "National award", "Women rendering distinguished services", "women", "MoWCD"),
        
        # Health (10)
        ("Ayushman Bharat - PMJAY", "आयुष्मान भारत", "Health cover of Rs. 5 lakhs per family", "Poor and vulnerable families", "health", "MoHFW"),
        ("National Health Mission", "राष्ट्रीय स्वास्थ्य मिशन", "Accessible healthcare", "All citizens", "health", "MoHFW"),
        ("Janani Suraksha Yojana", "जननी सुरक्षा योजना", "Cash assistance for institutional delivery", "Pregnant women", "health,women", "MoHFW"),
        ("National Tuberculosis Elimination Program", "राष्ट्रीय क्षय रोग उन्मूलन कार्यक्रम", "Free TB diagnosis and treatment", "TB patients", "health", "MoHFW"),
        ("Mission Indradhanush", "मिशन इंद्रधनुष", "Full immunization coverage", "Children under 2 years and pregnant women", "health,women", "MoHFW"),
        ("Rashtriya Swasthya Bima Yojana", "राष्ट्रीय स्वास्थ्य बीमा योजना", "Health insurance", "BPL workers in unorganized sector", "health", "MoHFW"),
        ("PM Swasthya Suraksha Yojana", "पीएम स्वास्थ्य सुरक्षा योजना", "Correcting regional imbalances in healthcare", "All citizens", "health", "MoHFW"),
        ("National AIDS Control Programme", "राष्ट्रीय एड्स नियंत्रण कार्यक्रम", "Prevention and control of HIV", "All citizens", "health", "MoHFW"),
        ("CGHS", "सीजीएचएस", "Comprehensive medical care", "Central Govt employees and pensioners", "health", "MoHFW"),
        ("ESIC Scheme", "ईएसआईसी योजना", "Medical and cash benefits", "Employees earning under Rs. 21,000/month", "health", "MoLE"),
        
        # Other - Housing, Pension, Livelihood (10)
        ("Pradhan Mantri Awas Yojana (Urban)", "पीएम आवास योजना (शहरी)", "Housing for all", "Urban poor, EWS, LIG", "housing,other", "MoHUA"),
        ("Pradhan Mantri Awas Yojana (Gramin)", "पीएम आवास योजना (ग्रामीण)", "Financial assistance for housing", "Rural poor", "housing,other", "MoRD"),
        ("Atal Pension Yojana", "अटल पेंशन योजना", "Guaranteed pension of Rs. 1000-5000", "Unorganized sector workers aged 18-40", "pension,other", "MoF"),
        ("Indira Gandhi National Old Age Pension", "इंदिरा गांधी राष्ट्रीय वृद्धावस्था पेंशन", "Rs. 200-500 per month", "BPL persons aged 60+", "pension,other", "MoRD"),
        ("Indira Gandhi National Widow Pension", "इंदिरा गांधी राष्ट्रीय विधवा पेंशन", "Rs. 300 per month", "BPL widows aged 40-59", "pension,women", "MoRD"),
        ("Indira Gandhi National Disability Pension", "इंदिरा गांधी राष्ट्रीय विकलांगता पेंशन", "Rs. 300 per month", "BPL persons with severe disabilities", "pension,health", "MoRD"),
        ("PM Shram Yogi Maan-dhan", "पीएम श्रम योगी मान-धन", "Rs. 3000/month pension", "Unorganized workers earning < Rs.15000", "pension,other", "MoLE"),
        ("MGNREGA", "मनरेगा", "100 days of wage employment", "Rural households", "other", "MoRD"),
        ("PM Mudra Yojana", "पीएम मुद्रा योजना", "Loans up to 10 lakhs", "Non-corporate, non-farm small/micro enterprises", "other", "MoF"),
        ("PM SVANidhi", "पीएम स्वनिधि", "Working capital loan up to Rs. 10,000", "Street vendors", "other", "MoHUA"),
        
        # Artisan/Craftsman (10)
        ("PM Vishwakarma Yojana", "पीएम विश्वकर्मा योजना", "Collateral-free credit, skill training, toolkit incentive", "Traditional artisans and craftspeople", "artisan,entrepreneur,business", "MSME"),
        ("Ambedkar Hastshilp Vikas Yojana", "अम्बेडकर हस्तशिल्प विकास योजना", "Promoting handicrafts and artisans", "Artisans", "artisan", "Ministry of Textiles"),
        ("SFURTI Scheme", "स्फूर्ति योजना", "Revamping traditional industries", "Artisans, rural entrepreneurs", "artisan,rural,business", "MSME"),
        ("PMEGP", "पीएमईजीपी", "Margin money subsidy for micro enterprises", "Unemployed youth, artisans", "artisan,entrepreneur,unemployed,business", "MSME"),
        ("KVIC Margin Money Scheme", "केवीआईसी मार्जिन मनी योजना", "Financial assistance for khadi and village industries", "Rural artisans", "artisan,village,rural", "MSME"),
        ("Handloom Weavers Comprehensive Welfare Scheme", "हथकरघा बुनकर कल्याण योजना", "Health and life insurance", "Handloom weavers", "artisan", "Ministry of Textiles"),
        ("National Handicraft Development Programme", "राष्ट्रीय हस्तशिल्प विकास कार्यक्रम", "Design and technology upgradation", "Handicraft artisans", "artisan", "Ministry of Textiles"),
        ("USTTAD Scheme", "उस्ताद योजना", "Upgrading skills in traditional arts/crafts", "Minority communities", "artisan,minority", "MoMA"),
        ("Gramodyog Vikas Yojana", "ग्रामोद्योग विकास योजना", "Promotion of village industries", "Traditional artisans", "artisan,village", "MSME"),
        ("Coir Vikas Yojana", "कॉयर विकास योजना", "Development of coir industry", "Coir workers", "artisan", "MSME"),

        # Women Entrepreneur (10)
        ("Mudra Yojana for Women", "महिलाओं के लिए मुद्रा योजना", "Loans up to 10 lakhs for women entrepreneurs", "Women entrepreneurs", "women,entrepreneur,business", "MoF"),
        ("TREAD Scheme", "ट्रेड योजना", "Trade related entrepreneurship assistance", "Women", "women,entrepreneur,business", "MSME"),
        ("Annapurna Scheme", "अन्नपूर्णा योजना", "Loans for women in food catering", "Women entrepreneurs", "women,business", "State/Banks"),
        ("Stree Shakti Package", "स्त्री शक्ति पैकेज", "Concession on interest rates for women", "Women entrepreneurs", "women,business", "SBI/Banks"),
        ("Bhartiya Mahila Bank Business Loan", "भारतीय महिला बैंक बिजनेस लोन", "Loans up to 20 crores for manufacturing", "Women entrepreneurs", "women,business", "Banks"),
        ("Dena Shakti Scheme", "देना शक्ति योजना", "Loans for agriculture, manufacturing, micro-credit", "Women entrepreneurs", "women,farmer,business", "Banks"),
        ("Udyogini Scheme", "उद्योगिनी योजना", "Loans at low interest rates", "Women entrepreneurs (low income)", "women,business", "State/Banks"),
        ("Cent Kalyani Scheme", "सेंट कल्याणी योजना", "Loans for new/existing businesses", "Women entrepreneurs", "women,business", "Central Bank"),
        ("Mahila Samridhi Yojana", "महिला समृद्धि योजना", "Microfinance for women", "Women from backward classes", "women,business", "MoSJ&E"),
        ("Women Entrepreneurship Platform (WEP)", "महिला उद्यमिता मंच", "Mentorship and funding access", "Women entrepreneurs", "women,business", "NITI Aayog"),

        # Youth Startup (10)
        ("Startup India Seed Fund", "स्टार्टअप इंडिया सीड फंड", "Financial assistance to startups", "Startups", "youth,business,entrepreneur", "DPIIT"),
        ("Stand-Up India for Youth", "युवाओं के लिए स्टैंड अप इंडिया", "Loans between 10 lakh and 1 crore", "SC/ST/Women/Youth", "youth,business", "MoF"),
        ("PM Kaushal Vikas Yojana", "पीएम कौशल विकास योजना", "Skill certification and training", "Unemployed youth", "youth,unemployed", "MSDE"),
        ("Atal Innovation Mission", "अटल नवाचार मिशन", "Promoting innovation and entrepreneurship", "Students, youth", "youth,student,business", "NITI Aayog"),
        ("National Apprenticeship Promotion Scheme", "राष्ट्रीय शिक्षुता संवर्धन योजना", "Apprenticeship training", "Youth", "youth,unemployed", "MSDE"),
        ("Deen Dayal Upadhyaya Grameen Kaushalya Yojana", "डीडीयू-जीकेवाई", "Placement-linked skill training", "Rural youth", "youth,rural,unemployed", "MoRD"),
        ("Software Technology Park Scheme", "सॉफ्टवेयर टेक्नोलॉजी पार्क योजना", "Export promotion for IT startups", "IT Entrepreneurs", "youth,business", "MeitY"),
        ("Venture Capital Scheme for Agri-Business", "कृषि व्यवसाय के लिए वेंचर कैपिटल", "Funding for agri-startups", "Agri-entrepreneurs", "youth,business,farmer", "SFAC"),
        ("Self Employment Scheme for Rehabilitation of Manual Scavengers", "मैनुअल स्कैवेंजर्स के पुनर्वास के लिए योजना", "Skill training and loans", "Manual scavengers/youth", "youth,business", "MoSJ&E"),
        ("Dairy Entrepreneurship Development Scheme", "डेयरी उद्यमिता विकास योजना", "Subsidy for dairy farms", "Youth, farmers", "youth,business,farmer", "NABARD"),

        # Disability (5)
        ("ADIP Scheme", "एडीआईपी योजना", "Assistance for purchase of aids/appliances", "Persons with disabilities", "health,disability", "MoSJ&E"),
        ("Deendayal Disabled Rehabilitation Scheme", "दीनदयाल विकलांग पुनर्वास योजना", "Rehabilitation services", "Persons with disabilities", "health,disability", "MoSJ&E"),
        ("National Fellowship for Persons with Disabilities", "विकलांग व्यक्तियों के लिए राष्ट्रीय फेलोशिप", "Fellowship for higher education", "Students with disabilities", "student,disability", "MoSJ&E"),
        ("Niramaya Health Insurance", "निरामय स्वास्थ्य बीमा", "Health insurance up to Rs. 1 lakh", "Persons with autism, CP, MR", "health,disability", "National Trust"),
        ("Scholarships for Students with Disabilities", "विकलांग छात्रों के लिए छात्रवृत्ति", "Financial aid for education", "Students with disabilities", "student,disability", "MoSJ&E"),

        # Senior Citizen (5)
        ("Pradhan Mantri Vaya Vandana Yojana", "पीएम वय वंदना योजना", "Assured return of 8%", "Senior citizens (60+)", "senior,pension", "LIC/MoF"),
        ("Rashtriya Vayoshri Yojana", "राष्ट्रीय वयोश्री योजना", "Physical aids and assisted living devices", "Senior citizens (BPL)", "senior,health", "MoSJ&E"),
        ("Senior Citizen Savings Scheme", "वरिष्ठ नागरिक बचत योजना", "High interest savings", "Senior citizens", "senior", "MoF"),
        ("Varishtha Pension Bima Yojana", "वरिष्ठ पेंशन बीमा योजना", "Pension scheme", "Senior citizens", "senior,pension", "LIC"),
        ("Vayoshrestha Samman", "वयोश्रेष्ठ सम्मान", "National awards for senior citizens", "Senior citizens / NGOs", "senior", "MoSJ&E")
    ]
    
    schemes = []
    for i, (name, name_hi, benefit, eligibility, tag_str, ministry) in enumerate(base_schemes):
        tags = tag_str.split(",")
        
        doc_text = f"Scheme Name: {name}\nBenefit: {benefit}\nEligibility: {eligibility}\nTags: {', '.join(tags)}"
        
        scheme_obj = {
            "id": f"SCHEME_HC_{i+1}",
            "name": name,
            "name_hi": name_hi,
            "benefit": benefit,
            "eligibility": eligibility,
            "documents": ["Aadhaar Card", "Bank Passbook", "Passport Size Photo"],
            "apply_link": f"https://www.india.gov.in/search/site/{name.replace(' ', '%20')}",
            "ministry": ministry,
            "tags": tags,
            "document_text": doc_text
        }
        schemes.append(scheme_obj)
        
    return schemes

def fetch_schemes_from_api():
    """Try fetching from MyScheme API."""
    print("Trying MyScheme API...")
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    payload = {
        "lang": "en",
        "query": "",
        "keyword": "",
        "sort": "relevance",
        "from": 0,
        "size": BATCH_SIZE
    }
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        schemes_batch = []
        if 'hits' in data and 'hits' in data['hits']:
            schemes_batch = data['hits']['hits']
        elif 'data' in data and 'schemes' in data['data']:
            schemes_batch = data['data']['schemes']
        elif isinstance(data.get('data'), list):
            schemes_batch = data['data']
            
        if not schemes_batch:
            print("API returned empty data.")
            return None
            
        formatted_schemes = []
        for i, item in enumerate(schemes_batch):
            source = item.get('_source', item)
            
            name = source.get('schemeName', '')
            short_title = source.get('schemeShortTitle', '')
            code = source.get('schemeCode', f"SCHEME_API_{i}")
            ministry = source.get('ministryName', 'Unknown Ministry')
            
            desc_raw = source.get('description', '') or source.get('benefit', '')
            elig_raw = source.get('eligibilityCriteria', '')
            docs_raw = source.get('documentsRequired', '')
            link = source.get('officialLink', '') or source.get('applyLink', '')
            
            benefit = clean_html(desc_raw)
            eligibility = clean_html(elig_raw)
            docs_text = clean_html(docs_raw)
            
            # Extract documents (fallback to Aadhaar if empty)
            documents = []
            if docs_text:
                docs_split = [d.strip() for d in re.split(r'\n|,', docs_text) if d.strip()]
                documents = docs_split[:5] if docs_split else ["Aadhaar Card"]
            else:
                documents = ["Aadhaar Card", "Bank Details"]
                
            # Extract tags based on text
            combined_text = f"{name} {benefit} {eligibility} {ministry}"
            tags = extract_tags(combined_text)
            
            doc_text = f"Scheme Name: {name}\nBenefit: {benefit}\nEligibility: {eligibility}\nTags: {', '.join(tags)}"
            
            scheme_obj = {
                "id": code,
                "name": name,
                "name_hi": short_title if short_title else name,
                "benefit": benefit,
                "eligibility": eligibility,
                "documents": documents,
                "apply_link": link,
                "ministry": ministry,
                "tags": tags,
                "document_text": doc_text
            }
            formatted_schemes.append(scheme_obj)
            
        print(f"Fetched {len(formatted_schemes)} schemes from API")
        return formatted_schemes
        
    except Exception as e:
        print(f"API failed with error: {e}")
        return None

def main():
    # 1. Try MyScheme API first
    schemes = fetch_schemes_from_api()
    
    # 2. If it fails, use backup data
    if not schemes:
        print("API failed, using backup data")
        schemes = get_hardcoded_schemes()
        print(f"Fetched {len(schemes)} schemes from backup data")
        
    print(f"Total schemes collected: {len(schemes)}")
    
    # 3. Always succeed and create schemes_raw.json
    output_file = os.path.join(os.path.dirname(__file__), "schemes_raw.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(schemes, f, indent=2, ensure_ascii=False)
        
    print("Saved to schemes_raw.json")
        
    # 4. Print summary
    total = len(schemes)
    categories = {"farmer": 0, "student": 0, "women": 0, "health": 0, "other": 0}
    
    for s in schemes:
        tags = s.get("tags", [])
        has_primary = False
        for tag in ["farmer", "student", "women", "health"]:
            if tag in tags:
                categories[tag] += 1
                has_primary = True
        
        if not has_primary or "other" in tags:
            categories["other"] += 1
            
    print("\nschemes_raw.json created successfully")
    print(f"Total schemes: {total}")
    print(f"Categories: farmer({categories['farmer']}), student({categories['student']}), "
          f"women({categories['women']}), health({categories['health']}), other({categories['other']})")

if __name__ == "__main__":
    main()
