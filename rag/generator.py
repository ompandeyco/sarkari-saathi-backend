import os
import json
import google.generativeai as genai

class AnswerGenerator:
    def __init__(self):
        print("Initializing AnswerGenerator...")
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Warning: GEMINI_API_KEY is not set in the environment.")
            
        # Configure Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def generate(self, user_profile: dict, retrieved_docs: list, lang: str = "en") -> dict:
        # 1. Truncate each scheme context to 200 chars and only send top 5 docs
        top_docs = retrieved_docs[:5]
        context_parts = []
        
        for doc in top_docs:
            name = doc.get("name", "Unknown")
            benefit = doc.get("benefit", "Not specified")
            eligibility = doc.get("eligibility", "Not specified")
            apply_link = doc.get("apply_link", "Not specified")
            
            context = f"Scheme: {name}\nBenefit: {benefit}\nEligibility: {eligibility}\nApply: {apply_link}"
            
            # Keep prompt under 2000 tokens by limiting each scheme context
            if len(context) > 200:
                context = context[:197] + "..."
            context_parts.append(context)
            
        formatted_context = "\n---\n".join(context_parts)
        
        prompt = f"""
You are matching government schemes for 
a specific Indian person.

PERSON PROFILE:
- Situation: {user_profile.get('situation')}
- Education: {user_profile.get('education')}  
- Location: {user_profile.get('location')}
- Phone access: {user_profile.get('has_phone')}
- Income target: {user_profile.get('target_earning')}

AVAILABLE SCHEMES (from database):
{formatted_context}

STRICT RULES:
1. Only return schemes that DIRECTLY match 
   this person's situation
2. A farmer should get farmer schemes
3. A student should get scholarship schemes
4. Village person should get rural schemes
5. DO NOT return the same generic schemes 
   for everyone
6. why_relevant must explain specifically 
   why THIS person qualifies

Return top 3-5 most relevant schemes as JSON.
Be strict — quality over quantity.

Return exactly this JSON format without markdown ticks:
{{
  "schemes": [
    {{
      "id": "scheme_code",
      "name_hi": "hindi name",
      "name_en": "english name",
      "benefit_hi": "benefit in hindi",
      "benefit_en": "benefit in english",
      "why_relevant_hi": "why matches user profile in hindi (1 sentence)",
      "why_relevant_en": "same in english (1 sentence)",
      "documents_needed": ["list"],
      "apply_link": "URL",
      "priority": "high/medium/low"
    }}
  ],
  "total_benefit_estimate": "number",
  "personalized_message_hi": "encouraging message in simple Hindi",
  "personalized_message_en": "same in English"
}}
"""

        full_prompt = prompt

        # 3. Call Gemini
        try:
            generation_config = genai.GenerationConfig(
                response_mime_type="application/json"
            )
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            # 4. Bulletproof JSON parsing
            text = response.text
            # Strip potential markdown formatting that sometimes escapes mime_type setting
            text = text.replace("```json", "")
            text = text.replace("```", "")
            text = text.strip()
            
            parsed_response = json.loads(text)
            return parsed_response
            
        except Exception as e:
            print(f"Error parsing Gemini response or API failure: {e}")
            return self._fallback_response(top_docs)

    def _fallback_response(self, docs: list) -> dict:
        """Safe Fallback response if Gemini API or parsing fails."""
        schemes = []
        for idx, doc in enumerate(docs):
            name = doc.get("name", "Unknown Scheme")
            benefit = doc.get("benefit", "No benefits specified")
            apply_link = doc.get("apply_link", "")
            
            schemes.append({
                "id": doc.get("id", f"fallback_{idx}"),
                "name_hi": name,
                "name_en": name,
                "benefit_hi": benefit,
                "benefit_en": benefit,
                "why_relevant_hi": "यह योजना आपके प्रोफाइल से मेल खाती है।",
                "why_relevant_en": "This scheme is a match for your profile.",
                "documents_needed": ["Aadhaar Card", "Bank Account Details"],
                "apply_link": apply_link,
                "priority": "medium"
            })
            
        return {
            "schemes": schemes,
            "total_benefit_estimate": 0,
            "personalized_message_hi": "क्षमा करें, एआई कनेक्शन काम नहीं कर रहा है, लेकिन ये शीर्ष योजनाएं आपके लिए सबसे प्रासंगिक हो सकती हैं।",
            "personalized_message_en": "Sorry, the AI generation failed, but these top retrieved schemes are highly relevant to you."
        }
