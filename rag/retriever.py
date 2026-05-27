import os
os.environ['HF_HOME'] = os.getenv(
    'HF_CACHE_DIR', 
    'D:\\omproject\\hf_cache'
)
os.environ['TRANSFORMERS_CACHE'] = os.getenv(
    'TRANSFORMERS_CACHE',
    'D:\\omproject\\hf_cache'
)
os.makedirs('D:\\omproject\\hf_cache', exist_ok=True)
import re
import chromadb
from sentence_transformers import SentenceTransformer

class SchemeRetriever:
    _instance = None
    _model = None
    _client = None
    _collection = None
    
    def __new__(cls):
        # Singleton pattern to ensure only one instance is created
        if cls._instance is None:
            cls._instance = super(SchemeRetriever, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Load model and DB only once
        if self._model is None:
            print("Initializing SchemeRetriever...")
            
            # Cache the model class-level to prevent reloading
            self.__class__._model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            
            # Relative path to chroma_db
            chroma_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "chroma_db"
            )
            
            self.__class__._client = chromadb.PersistentClient(path=chroma_path)
            
            try:
                self.__class__._collection = self._client.get_collection(name="govt_schemes")
                count = self.get_collection_size()
                print(f"Retriever initialized. {count} schemes indexed.")
            except Exception as e:
                print(f"Collection not found or empty: {e}")
                self.__class__._collection = None

    @property
    def model(self):
        return self.__class__._model

    @property
    def collection(self):
        return self.__class__._collection

    def profile_to_query(self, profile: dict) -> str:
        situation_map = {
            "no_job": "unemployed person needs work and income",
            "student_earning": "student wants part time earning",
            "farmer_extra": "farmer wants additional income support",
            "educated_unemployed": "graduate looking for job",
            "want_own_business": "wants to start own business",
            "restart": "lost job wants to restart career",
            "low_income_employed": "employed but low salary extra income"
        }
        education_map = {
            "below_8th": "primary education",
            "tenth": "10th pass matriculation",
            "twelfth": "12th pass intermediate",
            "graduate": "college graduate degree",
            "post_graduate": "post graduate masters"
        }
        location_map = {
            "village": "rural village area",
            "small_town": "small town semi-urban",
            "big_city": "urban metropolitan city"
        }
        
        situation = situation_map.get(
            profile.get('situation', ''), 
            profile.get('situation', '')
        )
        education = education_map.get(
            profile.get('education', ''),
            profile.get('education', '')
        )
        location = location_map.get(
            profile.get('location', ''),
            profile.get('location', '')
        )
        
        query = f"query: {situation} education {education} location {location}"
        return query
    def filter_by_profile(self, results, profile):
        situation = profile.get('situation','')
        education = profile.get('education','')
        location = profile.get('location','')
        
        # Score each result by profile match
        scored = []
        for i, doc in enumerate(results['documents'][0]):
            score = 0
            meta = results['metadatas'][0][i]
            tags = meta.get('tags', '').lower()
            
            # Situation matching
            if situation == 'farmer_extra' and 'farmer' in tags:
                score += 3
            if situation == 'student_earning' and 'student' in tags:
                score += 3
            if situation == 'no_job' and any(t in tags 
                for t in ['unemployed','daily_wage','rural']):
                score += 3
            if situation == 'want_own_business' and any(t in tags 
                for t in ['business','entrepreneur']):
                score += 3
                
            # Location matching
            if location == 'village' and 'rural' in tags:
                score += 2
            if location == 'big_city' and 'urban' in tags:
                score += 2
                
            # Education matching
            if education in ['below_8th','tenth'] and 'bpl' in tags:
                score += 1
            if education == 'graduate' and 'scholarship' in tags:
                score += 1
                
            # Always include universal schemes
            if 'all' in tags:
                score += 1
                
            scored.append((score, i, doc, meta, results['ids'][0][i], results['distances'][0][i]))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Return top 5 most relevant
        return [
            {
                'document': item[2],
                'metadata': item[3],
                'relevance_score': item[0],
                'id': item[4],
                'distance': item[5]
            }
            for item in scored[:5]
        ]

    def retrieve(self, user_profile: dict, top_k: int = 10) -> list:
        if not self.collection:
            return []
            
        query_text = self.profile_to_query(user_profile)
        
        # Encode query to vector
        embedding = self.model.encode(query_text, normalize_embeddings=True)
        
        results = self.collection.query(
            query_embeddings=[embedding.tolist()],
            n_results=min(top_k, 50)
        )
        
        filtered_results = self.filter_by_profile(results, user_profile)
        
        formatted_results = []
        if not filtered_results or len(filtered_results) == 0:
            return formatted_results
            
        for item in filtered_results:
            metadata = item['metadata']
            distance = item['distance']
            doc_text = item['document']
            scheme_id = item['id']
            
            # Since vectors are normalized, distance is directly related to cosine similarity
            similarity_score = 1.0 - (distance / 2.0)
            
            # Extract basic info
            name = metadata.get("name", "Unknown")
            benefit_str = metadata.get("benefit_amount", "Benefit unspecified")
            apply_link = metadata.get("apply_link", "")
            
            # Simple regex to extract eligibility safely
            eligibility_str = "Refer to official guidelines"
            elig_match = re.search(r'eligibility:\s*(.*?)\s*(?:ministry|tags):', doc_text)
            if elig_match:
                eligibility_str = elig_match.group(1).strip()
            
            # Format expected by main.py and generator.py
            formatted_results.append({
                "id": scheme_id,
                "name": name,
                "benefit": benefit_str,
                "eligibility": eligibility_str,
                "apply_link": apply_link,
                "score": round(similarity_score, 4),
                "document_text": doc_text
            })
            
        return formatted_results

    def get_collection_size(self) -> int:
        try:
            return self.collection.count() if self.collection else 0
        except:
            return 0
