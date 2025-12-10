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

    المدخلات:
        handler: كائن اتصال Neo4j.
        path_details: قائمة بالروابط التي تم استخدامها في الاستدلال الناجح/الفاشل.
        success_delta: إشارة التغذية الراجعة (Δ). 
                       (مثلاً: +1.0 للنجاح، -0.5 للفشل، أو 0.0 لعدم التأكيد).
        eta: معدل التعلم (η).
        
    المخرجات:
        قائمة بالروابط التي تم تحديثها.
    """
    
    updated_edges = []
    
    if success_delta == 0.0:
        return updated_edges # لا تحديث إذا لم يكن هناك تأكيد للنجاح/الفشل
    
    for edge in path_details:
        cause_name = edge['start']
        effect_name = edge['end']
        current_weight = edge['weight']
        
        # 1. تطبيق معادلة التحديث
        # w(t+1) = clip(w(t) + η * Δ, 0, 1)
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
            "new_weight": round(new_weight, 4) # تقريب الوزن للحفاظ على دقة قاعدة البيانات
        }
        
        # تنفيذ الاستعلام
        # result = handler.execute_query(query, parameters)
        # updated_edges.append(result[0]['elementId(r)']) # يمكن تسجيل الروابط المحدثة
        
        # كود وهمي للعرض:
        print(f"  [+] تحديث: {cause_name} -> {effect_name}. الوزن الجديد: {round(new_weight, 4)}")
        updated_edges.append(f"{cause_name}->{effect_name}")
        
    return updated_edges