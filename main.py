import os
import json 
from openai import OpenAI
from db.neo4j_handler import Neo4jHandler
from core.bridge import process_and_learn, attempt_innovative_solution
from core.verify_causal import verify_causal_path
import httpx 
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# ----------------------------------------------------------------------
# 1. إعدادات التهيئة (Configuration)
# ----------------------------------------------------------------------

# ⚠️ ملاحظة: يجب التأكد من صحة هذه القيم
# NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
NEO4J_URI = os.getenv("NEO4J_URI")
# NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_USER = os.getenv("NEO4J_USER")
# NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "123456Aa@")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# تهيئة العميل (مع محاولة تجاوز مشاكل الوكيل/TypeError)
try:
    http_client = httpx.Client()
    llm_client = OpenAI(api_key=OPENAI_API_KEY, http_client=http_client)

except TypeError:
    print("تحذير: فشلت التهيئة اليدوية للعميل، العودة إلى الطريقة التلقائية.")
    llm_client = OpenAI(api_key=OPENAI_API_KEY)

# تهيئة مُعالج قاعدة البيانات
neo4j_handler = Neo4jHandler(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

# ----------------------------------------------------------------------
# 2. وظيفة محاكاة استخراج الفرضية (للتشغيل في هذا المثال)
# ----------------------------------------------------------------------

def mock_extract_claims(scenario: str) -> str:
    """محاكاة استخراج الفرضية السببية كـ JSON (لتجنب استدعاء LLM حقيقي)."""
    if "slow database" in scenario:
        # السيناريو 1: مسار ناجح وموثوق
        return json.dumps({
            "causal_claims": [
                {"cause": "Database Query Slowdown", "effect": "High Latency"}
            ]
        })
    elif "CPU usage" in scenario:
        # السيناريو 2: مسار غير موثوق أو غير موجود
        return json.dumps({
            "causal_claims": [
                {"cause": "increase thread priority", "effect": "better performance"}
            ]
        })
    return json.dumps({"causal_claims": []})

# ----------------------------------------------------------------------
# 3. سيناريوهات التنفيذ المتكاملة
# ----------------------------------------------------------------------

def run_scenario_1_success_and_learn():
    """السيناريو 1: النجاح في التحقق، ثم التعلم لتعزيز الثقة."""
    print("==================================================")
    print("🧪 السيناريو 1: نجاح التحقق والتعزيز الإيجابي للثقة")
    print("==================================================")
    
    llm_output = mock_extract_claims("slow database") 
    
    # 2. العملية الرئيسية (التحقق والتعلم).
    result = process_and_learn(llm_output, neo4j_handler, llm_client, feedback_delta=1.0) 
    
    print(f"\n✅ النتيجة النهائية:")
    print(f"الحالة: {result['status']}")
    
    if 'message' in result:
        print(f"رسالة النظام: {result['message']}")
    elif 'question' in result:
        print(f"رسالة النظام: {result['question']}")

    if 'system_confidence' in result:
        print(f"مستوى الثقة الجديد: {result['system_confidence']}")
    

def run_scenario_2_failure_and_active_learning():
    """السيناريو 2: الفشل في التحقق، تفعيل التعلم النشط، وتقليل الثقة."""
    print("\n==================================================")
    print("🧠 السيناريو 2: فشل التحقق وتفعيل التعلم النشط")
    print("==================================================")
    
    llm_output = mock_extract_claims("CPU usage")
    
    result = process_and_learn(llm_output, neo4j_handler, llm_client, feedback_delta=0.0)
    
    print(f"\n❌ النتيجة النهائية:")
    print(f"الحالة: {result['status']}")
    
    if 'message' in result:
        print(f"رسالة النظام: {result['message']}")
    elif 'question' in result:
        print(f"السؤال الاستكشافي: {result['question']}")
        
    if result['status'] == "Failure - Causal Gap Found (Active Learning)":
        if 'action_required' in result:
             print(f"الإجراء المطلوب: {result['action_required']}")
    
    if 'system_confidence' in result:
        print(f"مستوى الثقة الجديد: {result['system_confidence']}")


def run_scenario_3_innovation_and_risk_awareness():
    """السيناريو 3: اللجوء إلى الابتكار وتقييم المخاطر."""
    print("\n==================================================")
    print("🚀 السيناريو 3: الابتكار الواعي بالمخاطر")
    print("==================================================")
    
    cause = "High Latency"
    effect = "User Frustration"
    
    result = attempt_innovative_solution(neo4j_handler, llm_client, cause, effect)
    
    print(f"\n🛠️ نتيجة الابتكار:")
    print(f"الحالة: {result['status']}")
    if result['status'] == "Innovative Solution Found":
        print(f"المسار المقترح: {result['path']}")
        print(f"تقييم المخاطر (Score): {result['risk_assessment']['risk_score']}")
        print(f"الآثار الجانبية: {result['risk_assessment']['side_effects']}")
    elif result['status'] == "Innovative Solution REJECTED":
        print(f"سبب الرفض: {result['message']}")
        print(f"تفاصيل المخاطر: {result['risk_details']}")
    
    
if __name__ == "__main__":
    
    # ⚠️ هام: تأكد من تشغيل ملف 'data/seed_knowledge.cypher' في Neo4j قبل التنفيذ
    print("--- بدء تشغيل OpenCausal (مع الوعي الذاتي) ---")
    
    try:
        run_scenario_1_success_and_learn()
        run_scenario_2_failure_and_active_learning()
        run_scenario_3_innovation_and_risk_awareness()
        
    except Exception as e:
        print(f"\n⚠️ حدث خطأ عام (قد يكون بسبب عدم تهيئة Neo4jHandler أو مفتاح OpenAI): {e}")
    finally:
        print("\n--- اكتملت دورات OpenCausal ---")





# import os
# import json 
# from openai import OpenAI
# from db.neo4j_handler import Neo4jHandler
# from core.bridge import process_and_learn, attempt_innovative_solution
# from core.verify_causal import verify_causal_path
# import httpx 
# from dotenv import load_dotenv

# # Load variables from .env file
# load_dotenv()

# # ----------------------------------------------------------------------
# # 1. إعدادات التهيئة (Configuration)
# # ----------------------------------------------------------------------

# # ⚠️ ملاحظة: يجب التأكد من صحة هذه القيم
# # NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
# NEO4J_URI = os.getenv("NEO4J_URI")
# # NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
# NEO4J_USER = os.getenv("NEO4J_USER")
# # NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "123456Aa@")
# NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
# # OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# # تهيئة العميل (مع محاولة تجاوز مشاكل الوكيل/TypeError)
# try:
#     http_client = httpx.Client()
#     llm_client = OpenAI(api_key=OPENAI_API_KEY, http_client=http_client)

# except TypeError:
#     print("تحذير: فشلت التهيئة اليدوية للعميل، العودة إلى الطريقة التلقائية.")
#     llm_client = OpenAI(api_key=OPENAI_API_KEY)

# # تهيئة مُعالج قاعدة البيانات
# neo4j_handler = Neo4jHandler(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

# # ----------------------------------------------------------------------
# # 2. وظيفة محاكاة استخراج الفرضية (للتشغيل في هذا المثال)
# # ----------------------------------------------------------------------

# def mock_extract_claims(scenario: str) -> str:
#     """محاكاة استخراج الفرضية السببية كـ JSON (لتجنب استدعاء LLM حقيقي)."""
#     if "slow database" in scenario:
#         # السيناريو 1: مسار ناجح وموثوق (في العادة)
#         return json.dumps({
#             "causal_claims": [
#                 {"cause": "Database Query Slowdown", "effect": "High Latency"}
#             ]
#         })
#     elif "CPU usage" in scenario:
#         # السيناريو 2: مسار غير موثوق أو غير موجود
#         return json.dumps({
#             "causal_claims": [
#                 {"cause": "increase thread priority", "effect": "better performance"}
#             ]
#         })
#     return json.dumps({"causal_claims": []})

# # ----------------------------------------------------------------------
# # 3. سيناريوهات التنفيذ المتكاملة
# # ----------------------------------------------------------------------

# def run_scenario_1_success_and_learn():
#     """السيناريو 1: النجاح في التحقق، ثم التعلم لتعزيز الثقة."""
#     print("==================================================")
#     print("🧪 السيناريو 1: نجاح التحقق والتعزيز الإيجابي للثقة")
#     print("==================================================")
#     # 1. محاكاة خرج LLM
#     llm_output = mock_extract_claims("slow database") 
    
#     # ⭐⭐ كود الضمان النهائي باستخدام 'execute_query' ⭐⭐
#     try:
#         neo4j_handler.execute_query("""
#             MATCH (s:State {name: 'Database Query Slowdown'}), (t:State {name: 'High Latency'})
#             MERGE (s)-[r:CAUSES]->(t)
#             SET r.weight = 0.98
#         """)
#         print(">> تم فرض وزن العلاقة على 0.98 لضمان نجاح السيناريو 1")
#     except Exception as e:
#         # إذا كان الخطأ هو عدم وجود 'execute_query'، فيجب فحص Neo4jHandler
#         print(f">> فشل فرض الوزن (تأكد من وجود execute_query في Neo4jHandler): {e}")
#     # ⭐⭐ نهاية كود الضمان ⭐⭐

#     # 2. العملية الرئيسية (التحقق والتعلم).
#     result = process_and_learn(llm_output, neo4j_handler, llm_client, feedback_delta=1.0) 
    
#     print(f"\n✅ النتيجة النهائية:")
#     print(f"الحالة: {result['status']}")
    
#     # ⭐⭐ تصحيح الطباعة (مرونة لقراءة 'message' أو 'question') ⭐⭐
#     if 'message' in result:
#         print(f"رسالة النظام: {result['message']}")
#     elif 'question' in result:
#         print(f"رسالة النظام: {result['question']}")

#     if 'system_confidence' in result:
#         print(f"مستوى الثقة الجديد: {result['system_confidence']}")
    

# def run_scenario_2_failure_and_active_learning():
#     """السيناريو 2: الفشل في التحقق، تفعيل التعلم النشط، وتقليل الثقة."""
#     print("\n==================================================")
#     print("🧠 السيناريو 2: فشل التحقق وتفعيل التعلم النشط")
#     print("==================================================")
    
#     llm_output = mock_extract_claims("CPU usage")
    
#     result = process_and_learn(llm_output, neo4j_handler, llm_client, feedback_delta=0.0)
    
#     print(f"\n❌ النتيجة النهائية:")
#     print(f"الحالة: {result['status']}")
    
#     # ⭐⭐ تصحيح الطباعة (مرونة لقراءة 'message' أو 'question') ⭐⭐
#     if 'message' in result:
#         print(f"رسالة النظام: {result['message']}")
#     elif 'question' in result:
#         print(f"السؤال الاستكشافي: {result['question']}")
        
#     if result['status'] == "Failure - Causal Gap Found (Active Learning)":
#         if 'action_required' in result:
#              print(f"الإجراء المطلوب: {result['action_required']}")
    
#     if 'system_confidence' in result:
#         print(f"مستوى الثقة الجديد: {result['system_confidence']}")


# def run_scenario_3_innovation_and_risk_awareness():
#     """السيناريو 3: اللجوء إلى الابتكار وتقييم المخاطر."""
#     print("\n==================================================")
#     print("🚀 السيناريو 3: الابتكار الواعي بالمخاطر")
#     print("==================================================")
    
#     cause = "High Latency"
#     effect = "User Frustration"
    
#     result = attempt_innovative_solution(neo4j_handler, llm_client, cause, effect)
    
#     print(f"\n🛠️ نتيجة الابتكار:")
#     print(f"الحالة: {result['status']}")
#     if result['status'] == "Innovative Solution Found":
#         print(f"المسار المقترح: {result['path']}")
#         print(f"تقييم المخاطر (Score): {result['risk_assessment']['risk_score']}")
#         print(f"الآثار الجانبية: {result['risk_assessment']['side_effects']}")
#     elif result['status'] == "Innovative Solution REJECTED":
#         print(f"سبب الرفض: {result['message']}")
#         print(f"تفاصيل المخاطر: {result['risk_details']}")
    
    
# if __name__ == "__main__":
    
#     # ⚠️ هام: تأكد من تشغيل ملف 'data/seed_knowledge.cypher' في Neo4j قبل التنفيذ
#     print("--- بدء تشغيل OpenCausal (مع الوعي الذاتي) ---")
    
#     try:
#         run_scenario_1_success_and_learn()
#         run_scenario_2_failure_and_active_learning()
#         run_scenario_3_innovation_and_risk_awareness()
        
#     except Exception as e:
#         print(f"\n⚠️ حدث خطأ عام (قد يكون بسبب عدم تهيئة Neo4jHandler أو مفتاح OpenAI): {e}")
#     finally:
#         print("\n--- اكتملت دورات OpenCausal ---")






# import os
# import json 
# from openai import OpenAI
# from db.neo4j_handler import Neo4jHandler
# from core.bridge import process_and_learn, attempt_innovative_solution
# from core.verify_causal import verify_causal_path
# import httpx 
# from dotenv import load_dotenv

# # Load variables from .env file
# load_dotenv()

# # ----------------------------------------------------------------------
# # 1. إعدادات التهيئة (Configuration)
# # ----------------------------------------------------------------------

# # ⚠️ ملاحظة: يجب التأكد من صحة هذه القيم
# NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
# NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
# NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "123456Aa@")
# # يُفترض أن مفتاح API صحيح في بيئة التشغيل الفعلية
# # OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# # تهيئة العميل (مع محاولة تجاوز مشاكل الوكيل/TypeError)
# try:
#     http_client = httpx.Client()
#     llm_client = OpenAI(api_key=OPENAI_API_KEY, http_client=http_client)

# except TypeError:
#     print("تحذير: فشلت التهيئة اليدوية للعميل، العودة إلى الطريقة التلقائية.")
#     llm_client = OpenAI(api_key=OPENAI_API_KEY)

# # تهيئة مُعالج قاعدة البيانات
# neo4j_handler = Neo4jHandler(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

# # ----------------------------------------------------------------------
# # 2. وظيفة محاكاة استخراج الفرضية (للتشغيل في هذا المثال)
# # ----------------------------------------------------------------------

# def mock_extract_claims(scenario: str) -> str:
#     """محاكاة استخراج الفرضية السببية كـ JSON (لتجنب استدعاء LLM حقيقي)."""
#     if "slow database" in scenario:
#         # السيناريو 1: مسار ناجح وموثوق (في العادة)
#         return json.dumps({
#             "causal_claims": [
#                 {"cause": "Database Query Slowdown", "effect": "High Latency"}
#             ]
#         })
#     elif "CPU usage" in scenario:
#         # السيناريو 2: مسار غير موثوق أو غير موجود
#         return json.dumps({
#             "causal_claims": [
#                 {"cause": "increase thread priority", "effect": "better performance"}
#             ]
#         })
#     return json.dumps({"causal_claims": []})

# # ----------------------------------------------------------------------
# # 3. سيناريوهات التنفيذ المتكاملة
# # ----------------------------------------------------------------------

# def run_scenario_1_success_and_learn():
#     """السيناريو 1: النجاح في التحقق، ثم التعلم لتعزيز الثقة."""
#     print("==================================================")
#     print("🧪 السيناريو 1: نجاح التحقق والتعزيز الإيجابي للثقة")
#     print("==================================================")
    
#     llm_output = mock_extract_claims("slow database") 
    
#     # 2. العملية الرئيسية (التحقق والتعلم).
#     result = process_and_learn(llm_output, neo4j_handler, llm_client, feedback_delta=1.0) 
    
#     print(f"\n✅ النتيجة النهائية:")
#     print(f"الحالة: {result['status']}")
    
#     # ⭐⭐ تصحيح الطباعة (للتأكد من عدم وجود 'meessage' وللتعامل مع مفتاح 'question') ⭐⭐
#     if 'message' in result:
#         print(f"رسالة النظام: {result['message']}")
#     elif 'question' in result:
#         print(f"رسالة النظام: {result['question']}")

#     if 'system_confidence' in result:
#         print(f"مستوى الثقة الجديد: {result['system_confidence']}")
    

# def run_scenario_2_failure_and_active_learning():
#     """السيناريو 2: الفشل في التحقق، تفعيل التعلم النشط، وتقليل الثقة."""
#     print("\n==================================================")
#     print("🧠 السيناريو 2: فشل التحقق وتفعيل التعلم النشط")
#     print("==================================================")
    
#     llm_output = mock_extract_claims("CPU usage")
    
#     result = process_and_learn(llm_output, neo4j_handler, llm_client, feedback_delta=0.0)
    
#     print(f"\n❌ النتيجة النهائية:")
#     print(f"الحالة: {result['status']}")
    
#     # ⭐⭐ تصحيح الطباعة (للسيناريو 2) ⭐⭐
#     if 'message' in result:
#         print(f"رسالة النظام: {result['message']}")
#     elif 'question' in result:
#         print(f"السؤال الاستكشافي: {result['question']}")
        
#     if result['status'] == "Failure - Causal Gap Found (Active Learning)":
#         if 'action_required' in result:
#              print(f"الإجراء المطلوب: {result['action_required']}")
    
#     if 'system_confidence' in result:
#         print(f"مستوى الثقة الجديد: {result['system_confidence']}")


# def run_scenario_3_innovation_and_risk_awareness():
#     """السيناريو 3: اللجوء إلى الابتكار وتقييم المخاطر."""
#     print("\n==================================================")
#     print("🚀 السيناريو 3: الابتكار الواعي بالمخاطر")
#     print("==================================================")
    
#     cause = "High Latency"
#     effect = "User Frustration"
    
#     result = attempt_innovative_solution(neo4j_handler, llm_client, cause, effect)
    
#     print(f"\n🛠️ نتيجة الابتكار:")
#     print(f"الحالة: {result['status']}")
#     if result['status'] == "Innovative Solution Found":
#         print(f"المسار المقترح: {result['path']}")
#         print(f"تقييم المخاطر (Score): {result['risk_assessment']['risk_score']}")
#         print(f"الآثار الجانبية: {result['risk_assessment']['side_effects']}")
#     elif result['status'] == "Innovative Solution REJECTED":
#         print(f"سبب الرفض: {result['message']}")
#         print(f"تفاصيل المخاطر: {result['risk_details']}")
    
    
# if __name__ == "__main__":
    
#     # ⚠️ هام: تأكد من تشغيل ملف 'data/seed_knowledge.cypher' في Neo4j قبل التنفيذ
#     print("--- بدء تشغيل OpenCausal (مع الوعي الذاتي) ---")
    
#     try:
#         run_scenario_1_success_and_learn()
#         run_scenario_2_failure_and_active_learning()
#         run_scenario_3_innovation_and_risk_awareness()
        
#     except Exception as e:
#         print(f"\n⚠️ حدث خطأ عام (قد يكون بسبب عدم تهيئة Neo4jHandler أو مفتاح OpenAI): {e}")
#     finally:
#         print("\n--- اكتملت دورات OpenCausal ---")
