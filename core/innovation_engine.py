from db.neo4j_handler import Neo4jHandler
from typing import Optional, List, Dict

# Hyperparameters (يمكن تعديلها)
MAX_INNOVATION_PATH_LENGTH = 7  # السماح بمسارات أطول (أكثر ابتكاراً)
MIN_W_FOR_INNOVATION = 0.1      # الحد الأدنى لوزن الرابط المسموح به في الابتكار

def find_innovative_path(
    handler: Neo4jHandler, 
    start_entity: str, 
    target_goal: str, 
    constraints_to_ignore: List[str]
) -> Optional[Dict]:
    """
    يطبق مشغل imagine(I) للبحث عن مسار سببي بين Start و Target،
    مع تجاهل القيود (I) التي تمنع الحل عادةً.
    
    المدخلات:
        handler: كائن اتصال Neo4j.
        start_entity: نقطة البدء في الابتكار.
        target_goal: الهدف المراد تحقيقه.
        constraints_to_ignore: قائمة بأسماء العقد (القيود) التي يجب تعليقها مؤقتاً (I).
        
    المخرجات:
        أقصر مسار سببي ينجح في تجاوز القيود، أو None.
    """

    # 1. تحديد العقد التي يجب تجاهلها (I)
    ignored_nodes_cypher = "WHERE NOT n.name IN $constraints_to_ignore"

    # 2. صياغة استعلام Cypher للبحث عن المسار المبتكر
    query = f"""
    MATCH (start {{name: $start_entity}}), (target {{name: $target_goal}})
    
    MATCH p=(start)-[r:CAUSES*1..{MAX_INNOVATION_PATH_LENGTH}]->(target)
    
    WHERE all(n IN nodes(p) WHERE NOT n.name IN $constraints_to_ignore)
    
    AND all(r_edge IN relationships(p) WHERE r_edge.weight >= {MIN_W_FOR_INNOVATION})
    
    WITH 
        p, 
        reduce(w = 1.0, r IN relationships(p) | w * r.weight) AS path_weight
    
    RETURN 
        path_weight, 
        [r IN relationships(p) | {{start: startNode(r).name, end: endNode(r).name, weight: r.weight}}] AS path_details,
        length(p) AS path_length
    ORDER BY length(p) ASC, path_weight DESC 
    LIMIT 1
    """

    parameters = {
        "start_entity": start_entity,
        "target_goal": target_goal,
        "constraints_to_ignore": constraints_to_ignore
    }
    
    results = handler.execute_query(query, parameters)

    if results:
        # وجدنا مساراً ابتكارياً!
        print(f"🎉 تم اكتشاف مسار ابتكاري بطول {results[0]['path_length']} وبوزن {results[0]['path_weight']:.4f}")
        return results[0]
    else:
        # لم يتم العثور على حل حتى بعد تجاوز القيود
        return None