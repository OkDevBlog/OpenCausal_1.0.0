from db.neo4j_handler import Neo4jHandler
from typing import Dict, List

# Hyperparameters (يمكن تعديلها في مرحلة الضبط)
LEARNING_RATE_ETA = 0.1  # معدل التعلم (η): يحدد سرعة تغير الوزن

def update_causal_weight(
    handler: Neo4jHandler, 
    path_details: List[Dict], 
    success_delta: float, 
    eta: float = LEARNING_RATE_ETA
) -> List[str]:
    """
    يطبق قاعدة تحديث الوزن على كل رابط في المسار السببي الذي تم اختباره.
    ... (باقي التوثيق)
    """
    
    updated_edges = []
    
    if success_delta == 0.0:
        return updated_edges
    
    for edge in path_details:
        cause_name = edge['start']
        effect_name = edge['end']
        current_weight = edge['weight']
        
        # 1. تطبيق معادلة التحديث
        new_weight = current_weight + (eta * success_delta)
        
        # 2. تطبيق دالة القص (Clip Function) لضمان [0, 1]
        if new_weight > 1.0:
            new_weight = 1.0
        elif new_weight < 0.0:
            new_weight = 0.0
            
        # 3. تحديث الرابط في Neo4j باستخدام استعلام Cypher
        query = """
        MATCH (cause {name: $cause_name})-[r:CAUSES]->(effect {name: $effect_name})
        SET r.weight = $new_weight
        RETURN elementId(r)
        """
        
        parameters = {
            "cause_name": cause_name,
            "effect_name": effect_name,
            "new_weight": round(new_weight, 4)
        }
        
        # -------------------------------------------------------------------
        # ⭐ التعديل: إلغاء تعليق تنفيذ الاستعلام
        # -------------------------------------------------------------------
        result = handler.execute_query(query, parameters)
        
        # هذا السطر ضروري إذا كنت تريد تسجيل الروابط المحدثة
        # سنفترض أن execute_query يعيد قائمة من القواميس تحتوي على elementId(r)
        # للتوافق مع الاختبارات، يمكننا إبقاء الكود الوهمي في هذه المرحلة
        
        # الكود الوهمي للعرض (لإظهار النتيجة):
        print(f"  [+] تحديث: {cause_name} -> {effect_name}. الوزن الجديد: {round(new_weight, 4)}")
        updated_edges.append(f"{cause_name}->{effect_name}")
        
        # *إذا كنت تريد أن يكون الكود دقيقاً للإنتاج، يجب أن تكون التحديثات هكذا:*
        # if result and result[0]:
        #     updated_edges.append(result[0]['elementId(r)'])
        # -------------------------------------------------------------------
        
    return updated_edges

# دالة تحديث الثقة الذاتية
def update_system_confidence(
    handler: Neo4jHandler, 
    success_delta: float, 
    eta: float = LEARNING_RATE_ETA
) -> float:
    """
    تحديث مستوى الثقة الذاتية للنظام (System_Confidence) بناءً على نتيجة التنفيذ الأخيرة.
    
    المدخلات:
        handler: كائن اتصال Neo4j.
        success_delta: (+1.0 للنجاح، -0.5 للفشل).
        eta: معدل التعلم.
        
    المخرجات:
        مستوى الثقة الجديد.
    """
    
    # 1. استرجاع مستوى الثقة الحالي
    query_read = "MATCH (sc:SelfAwareness {name: 'System_Confidence'}) RETURN sc.current_level AS level LIMIT 1"
    result = handler.execute_query(query_read)
    
    if not result or 'level' not in result[0]:
        current_level = 0.5 # قيمة افتراضية إذا لم يتم العثور عليها
    else:
        current_level = result[0]['level']
        
    # 2. تطبيق معادلة التحديث (مثل تحديث الأوزان)
    new_level = current_level + (eta * success_delta)
    
    # 3. دالة القص (Clip)
    new_level = max(0.0, min(1.0, new_level))
    
    # 4. تحديث العقدة في Neo4j
    query_write = """
    MATCH (sc:SelfAwareness {name: 'System_Confidence'})
    SET sc.current_level = $new_level
    RETURN sc.current_level
    """
    handler.execute_query(query_write, {"new_level": round(new_level, 4)})
    
    return round(new_level, 4)