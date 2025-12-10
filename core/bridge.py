import json
from openai import OpenAI # مثال على استخدام LLM
from typing import List, Dict
from db.neo4j_handler import Neo4jHandler
from .innovation_engine import find_innovative_path
from .verify_causal import verify_causal_path # تم افتراض وجود TRUST_THRESHOLD هنا
from .weights import update_system_confidence, update_causal_weight

# يجب تهيئة العميل في مكان مناسب
# client = OpenAI(api_key=...) 

# 1. تصميم هيكل البيانات المتوقع (JSON Schema)
CAUSAL_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "cause": {"type": "string", "description": "اسم الشيء الذي يسبب الفعل أو الحالة."},
            "effect": {"type": "string", "description": "اسم النتيجة أو الحالة الناتجة."},
            "claim_type": {"type": "string", "description": "نوع العلاقة المزعومة (مثل: CAUSES، PREVENTS، ENABLES)."}
        },
        "required": ["cause", "effect"]
    }
}

# ------------------------------------------------------------------
# الدوال المساعدة (تبقى كما هي تقريبا)
# ------------------------------------------------------------------

def extract_causal_claims_from_llm(llm_output_text: str, client: OpenAI) -> List[Dict]:
    """يستخدم LLM لتحليل نص الإجابة واستخلاص الفرضيات السببية المنظمة."""
    # ... (الكود يبقى كما هو. ملاحظة: يجب أن يعيد 'claims' مباشرة، وليس claims.get("claims", []))
    system_prompt = ("أنت محلل منطقي متخصص. ...")
    user_content = f"النص لتحليله: '{llm_output_text}'"

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo", 
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_content}],
            response_format={"type": "json_object"}, 
        )
        raw_json_output = response.choices[0].message.content
        claims_data = json.loads(raw_json_output)
        
        # افتراض أن الخرج هو قائمة مباشرة أو داخل مفتاح 'claims'
        if isinstance(claims_data, list):
            return claims_data
        elif isinstance(claims_data, dict) and 'claims' in claims_data:
            return claims_data['claims']
        
        return []

    except Exception as e:
        print(f"حدث خطأ في استخلاص الفرضيات من LLM: {e}")
        return []
    

def generate_exploratory_question(llm_client: OpenAI, cause: str, effect: str, threshold: float) -> str:
    """يولد سؤالاً موجهاً للمستخدم لطلب معلومات سببية محددة بين السبب والنتيجة."""
    # ... (الكود يبقى كما هو)
    system_prompt = ("أنت محقق متخصص في المنطق السببي. ...")
    user_content = (f"المشكلة: لا أستطيع إثبات منطقياً أن '{cause}' يؤدي إلى '{effect}' "
                    f"لأن الروابط الحالية ضعيفة جداً. ما هو الإجراء المفقود الذي يجب أن أسأل عنه؟")

    try:
        response = llm_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_content}]
        )
        question = response.choices[0].message.content
        print(f"**[GAP ALERT]** تم اكتشاف فجوة سببية بين {cause} و {effect}. Thresh={threshold}")
        return f"نحتاج للمساعدة في إغلاق الفجوة المعرفية: {question}"

    except Exception as e:
        return f"عذراً، لا يمكنني صياغة سؤال استكشافي الآن بسبب خطأ في LLM: {e}"


# ------------------------------------------------------------------
# 2. المنطق الرئيسي للجسر (process_and_learn)
# ------------------------------------------------------------------

def process_and_learn(llm_text: str, handler: Neo4jHandler, llm_client: OpenAI, feedback_delta: float = 0.0):
    """
    الدالة الرئيسية التي تستخلص الفرضيات، تتحقق منها، وتدير دورة التعلم والوعي الذاتي.
    """
    
    # 1. استخلاص الفرضيات من النص
    causal_claims = extract_causal_claims_from_llm(llm_text, llm_client) 
    
    verified_path = None
    best_claim = None
    
    if causal_claims:
        # نبحث عن أول فرضية يمكن التحقق منها
        best_claim = causal_claims[0] 
        verified_path = verify_causal_path(handler, best_claim['cause'], best_claim['effect'])
    
    # ------------------------------------------------------------------
    # 2. اتخاذ القرار بعد التحقق وتطبيق التعلم والوعي الذاتي
    # ------------------------------------------------------------------
    
    if verified_path:
        # حالة النجاح: تم التحقق منطقياً
        
        # ⭐ 2.1. تطبيق التعلم (إذا كانت هناك تغذية راجعة)
        if feedback_delta != 0.0:
            update_causal_weight(handler, verified_path['path_details'], feedback_delta)
            
        # ⭐ 2.2. تحديث الوعي الذاتي (النجاح يعزز الثقة)
        new_confidence = update_system_confidence(handler, success_delta=0.1) # تعزيز بسيط
        
        return {
            "status": "Success - Logically Verified and Learned",
            "message": "تم تأكيد المنطق السببي. يمكن تنفيذ القرار بأمان.",
            "system_confidence": new_confidence
        }
    
    else:
        # حالة الفشل: اكتشاف فجوة سببية (Hallucination Prevention)
        
        # ⭐ 2.3. تحديث الوعي الذاتي (الفشل يقلل الثقة)
        new_confidence = update_system_confidence(handler, success_delta=-0.2) # تقليل الثقة عند الفشل في التحقق
        
        if best_claim:
            # 2.4. توليد سؤال للتعلم النشط
            gap_question = generate_exploratory_question(
                llm_client, 
                best_claim['cause'], 
                best_claim['effect'], 
                verify_causal_path.TRUST_THRESHOLD
            )
            return {
                "status": "Failure - Causal Gap Found (Active Learning)",
                "action_required": "طلب معلومات من المستخدم",
                "question": gap_question,
                "system_confidence": new_confidence
            }
        else:
            return {
                "status": "Failure - No Claims Found", 
                "message": "لم يتم العثور على فرضيات سببية للتحقق منها.",
                "system_confidence": new_confidence
            }


def attempt_innovative_solution(handler: Neo4jHandler, llm_client: OpenAI, original_cause: str, desired_effect: str):
    # ... (الكود يبقى كما هو)
    # 1. تحديد القيود
    constraints_to_ignore = ["High_Cost", "Slow_Protocol_K", "Mandatory_Check_J"]
    
    print(f"\n[🚀 INNOVATION MODE] تحويل التفكير للبحث عن حل يتجاهل: {constraints_to_ignore}")
    
    # 2. تطبيق مشغل imagine(I)
    innovative_path = find_innovative_path(
        handler,
        start_entity=original_cause,
        target_goal=desired_effect,
        constraints_to_ignore=constraints_to_ignore
    )
    
    if innovative_path:
        return {
            "status": "Innovative Solution Found",
            "path": innovative_path['path_details'],
            "risk_assessment": "مطلوب تحليل مخاطر عاجل."
        }
    else:
        return {"status": "Innovation Failed", "message": "لم يتم العثور على حل ابتكاري قابل للتطبيق."}