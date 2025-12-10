import json
from openai import OpenAI # مثال على استخدام LLM
from typing import List, Dict
from db.neo4j_handler import Neo4jHandler

# يجب تهيئة العميل في مكان مناسب (مثل ملف تهيئة عام)
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

# تحديث دالة process_llm_output في core/bridge.py (هيكل جديد)

from .verify_causal import verify_causal_path
from .weights import update_causal_weight

# تحديث الدالة الرئيسية في core/bridge.py

from .verify_causal import verify_causal_path
# ... استيراد دالة extract_causal_claims_from_llm ...

def process_llm_output(llm_text: str, handler: Neo4jHandler, llm_client: OpenAI):
    """
    المنطق الرئيسي للجسر: يستخلص الفرضيات ويتحقق منها سببيًا.
    """
    
    # 1. استخلاص الفرضيات من النص (الطبقة العصبية)
    causal_claims = extract_causal_claims_from_llm(llm_text, llm_client) 
    
    verified_claims = []
    
    for claim in causal_claims:
        # 2. التحقق من كل فرضية ضد الذاكرة Z (الطبقة الطوبولوجية)
        verified_path = verify_causal_path(handler, claim['cause'], claim['effect'])
        
        if verified_path:
            # 3. قبول الفرضية الموثوقة
            claim['is_verified'] = True
            claim['weight'] = verified_path['path_weight']
            verified_claims.append(claim)
        else:
            # 4. رفض الفرضية الضعيفة أو الكاذبة
            claim['is_verified'] = False
            verified_claims.append(claim)
    
    # 5. بناء الإجابة النهائية بناءً على النتائج المتحقق منها
    if verified_claims:
        # هنا يمكن استخدام الـ LLM مرة أخرى لصياغة إجابة نهائية دقيقة ومتحقق منها
        # أو يمكن الاكتفاء بالروابط المؤكدة في هذه المرحلة
        return {
            "status": "Success - Logically Verified",
            "verified_claims": verified_claims,
            "raw_llm_output": llm_text
        }
    else:
        # يتم تفعيل آلية التعلم النشط (طرح الأسئلة) إذا لم يتم التحقق من أي شيء
        return {
            "status": "Failure - Causal Gaps Found",
            "suggestion": "يجب طرح سؤال استكشافي لسد الفجوة في الذاكرة السببية Z."
        }
    
# تحديث دالة process_llm_output في core/bridge.py (هيكل جديد)
# تحديث الدالة الرئيسية process_and_learn في core/bridge.py

def process_and_learn(llm_text: str, handler: Neo4jHandler, llm_client: OpenAI, feedback_delta: float = 0.0):
    
    # ... (1. استخلاص الفرضيات) ...
    causal_claims = extract_causal_claims_from_llm(llm_text, llm_client) 
    
    # ... (2. التحقق من الفرضيات واختيار المسار الأمثل) ...
    # نفترض هنا أننا نبحث فقط عن أول فرضية (لتبسيط المثال)
    
    verified_path = None
    if causal_claims:
        claim = causal_claims[0]
        verified_path = verify_causal_path(handler, claim['cause'], claim['effect'])
    
    # ------------------------------------------------------------------
    # 3. اتخاذ القرار بعد التحقق
    # ------------------------------------------------------------------
    if verified_path:
        # إذا تم التحقق بنجاح
        # ... (مرحلة التعلم والـ update_causal_weight إذا كانت هناك تغذية راجعة) ...
        return {
            "status": "Success - Logically Verified",
            "message": "تم تأكيد المنطق السببي. يمكن تنفيذ القرار بأمان."
        }
    else:
        # إذا فشل التحقق (اكتشاف الفجوة السببية)
        
        # 4. توليد سؤال للتعلم النشط
        if causal_claims:
            gap_question = generate_exploratory_question(
                llm_client, 
                claim['cause'], 
                claim['effect'], 
                verify_causal_path.TRUST_THRESHOLD # استخدام العتبة من دالة التحقق
            )
            return {
                "status": "Failure - Causal Gap Found (Active Learning)",
                "action_required": "طلب معلومات من المستخدم",
                "question": gap_question
            }
        else:
             return {"status": "Failure - No Claims Found", "message": "لم يتم العثور على فرضيات سببية للتحقق منها."}


def extract_causal_claims_from_llm(llm_output_text: str, client: OpenAI) -> List[Dict]:
    """
    يستخدم LLM لتحليل نص الإجابة واستخلاص الفرضيات السببية المنظمة (Causes, Effects).
    
    المدخلات:
        llm_output_text: الإجابة الأولية المقترحة من LLM.
        client: كائن العميل الخاص بـ LLM.
        
    المخرجات:
        قائمة بفرضيات {cause, effect, claim_type}.
    """
    
    # 2. بناء أمر التحريض (Prompt)
    system_prompt = (
        "أنت محلل منطقي متخصص. مهمتك هي تحليل النص التالي واستخلاص جميع العلاقات السببية "
        "(السبب والنتيجة) الواردة فيه. يجب أن يكون الناتج بصيغة JSON يتطابق تمامًا مع الهيكل المقدم."
    )
    
    # دمج النص الذي يجب تحليله
    user_content = f"النص لتحليله: '{llm_output_text}'"

    try:
        # 3. إرسال الطلب للنموذج (باستخدام أدوات استدعاء الوظائف لتنظيم JSON)
        response = client.chat.completions.create(
            model="gpt-4-turbo",  # يفضل نموذج قوي لتنظيم JSON بدقة
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            # استخدام تقنية JSON mode أو tools/functions إذا كانت متاحة لضمان تنسيق الخرج
            response_format={"type": "json_object"}, 
            # *ملاحظة: في هذا المثال، نفترض أن النموذج سيخرج JSON بشكل مباشر*
        )
        
        # 4. تحليل الخرج
        raw_json_output = response.choices[0].message.content
        claims = json.loads(raw_json_output)
        
        # قد نحتاج إلى بعض التنظيف أو التحقق من صحة Schema
        return claims.get("claims", []) # نفترض أن الخرج قد يحتوي على مفتاح رئيسي 'claims'

    except Exception as e:
        print(f"حدث خطأ في استخلاص الفرضيات من LLM: {e}")
        return []
    

def generate_exploratory_question(
    llm_client: OpenAI, 
    cause: str, 
    effect: str, 
    threshold: float
) -> str:
    """
    يولد سؤالاً موجهاً للمستخدم لطلب معلومات سببية محددة بين السبب والنتيجة.

    المدخلات:
        llm_client: كائن العميل الخاص بـ LLM.
        cause: السبب الذي لم يتم التحقق منه.
        effect: النتيجة التي لم يتم التحقق منها.
        threshold: عتبة الثقة (tau) التي لم يتم الوصول إليها.

    المخرجات:
        سؤال استكشافي محدد.
    """
    
    system_prompt = (
        "أنت محقق متخصص في المنطق السببي. مهمتك هي صياغة سؤال دقيق جداً للمستخدم "
        "لطلب معلومة محددة تسد فجوة بين [السبب] و [النتيجة]. يجب أن يركز السؤال على "
        "البروتوكول أو الخطوة المفقودة التي تربطهما."
    )
    
    user_content = (
        f"المشكلة: لا أستطيع إثبات منطقياً أن '{cause}' يؤدي إلى '{effect}' "
        f"لأن الروابط الحالية ضعيفة جداً. ما هو الإجراء المفقود الذي يجب أن أسأل عنه؟"
    )

    try:
        response = llm_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
        )
        
        # 1. تحليل الإجابة وتضمينها
        question = response.choices[0].message.content
        
        # 2. تحديد الفجوة في الذاكرة (للتوثيق الداخلي)
        print(f"**[GAP ALERT]** تم اكتشاف فجوة سببية بين {cause} و {effect}. Thresh={threshold}")
        
        return f"نحتاج للمساعدة في إغلاق الفجوة المعرفية: {question}"

    except Exception as e:
        return f"عذراً، لا يمكنني صياغة سؤال استكشافي الآن بسبب خطأ في LLM: {e}"