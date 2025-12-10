from db.neo4j_handler import Neo4jHandler
from typing import Optional, List, Dict

# عتبة الثقة (Tau): أي مسار أقل من هذا الوزن لا يُعتبر سببيًا موثوقًا به
TRUST_THRESHOLD = 0.5

def verify_causal_path(
    handler: Neo4jHandler, 
    cause_name: str, 
    effect_name: str, 
    threshold: float = TRUST_THRESHOLD
) -> Optional[Dict]:
    """
    يبحث عن أقوى مسار سببي موجه وموزون بين سبب ونتيجة في الذاكرة Z.
    
    المدخلات:
        handler: كائن اتصال Neo4j.
        cause_name: اسم العقدة المسببة (e.g., "ارتفاع درجة الحرارة").
        effect_name: اسم العقدة الناتجة (e.g., "فشل الخادم").
        threshold: الحد الأدنى لوزن الرابط المطلوب (tau).
        
    المخرجات:
        مسار سببي موثوق به (كقائمة من الروابط والأوزان)، أو None إذا لم يتم العثور عليه.
    """

    # 1. صياغة استعلام Cypher للبحث عن المسار
    # نستخدم Dijkstra's algorithm (أو مسار أقصر مع تعديل) للبحث عن أقوى المسارات،
    # لكن للتبسيط الأولي نستخدم MATCH بسيط مع شرط الوزن.

    query = f"""
    MATCH (cause {{name: $cause_name}}), (effect {{name: $effect_name}})
    
    # ابحث عن المسارات بطول 1 إلى 5 روابط سببية
    MATCH p=shortestPath((cause)-[:CAUSES*1..5]->(effect))
    
    # حساب قوة المسار (منتج الأوزان) - التحدي الرياضي
    # *ملاحظة: منتج الأوزان يتم حسابه خارج Cypher لتعقيده الرياضي، لكن هنا نتحقق من الشروط الأساسية:*
    
    WITH 
        p, 
        reduce(w = 1.0, r IN relationships(p) | w * r.weight) AS path_weight
    
    # شرط القبول: يجب أن يكون الوزن الإجمالي للمسار أعلى من عتبة الثقة (tau)
    WHERE path_weight >= $threshold
    
    RETURN 
        path_weight, 
        [r IN relationships(p) | {{start: startNode(r).name, end: endNode(r).name, weight: r.weight}}] AS path_details
    ORDER BY path_weight DESC 
    LIMIT 1
    """

    parameters = {
        "cause_name": cause_name,
        "effect_name": effect_name,
        "threshold": threshold
    }
    
    results = handler.execute_query(query, parameters)

    if results:
        # وجدنا مسارًا سببيًا موثوقًا به
        return results[0]
    else:
        # لم يتم العثور على مسار يفي بالحد الأدنى للوزن (الاستنتاج غير موثوق به)
        return None