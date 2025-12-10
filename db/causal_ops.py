# استخدام دالة execute_query من الـ Handler

def create_causal_link(cause_name, cause_type, effect_name, effect_type, initial_weight=0.5):
    """
    ينشئ عقدتين ورابطاً سببيًا موجهًا وموزونًا بينهما.
    """
    query = """
    MERGE (cause:{cause_type} {{name: $cause_name}})
    MERGE (effect:{effect_type} {{name: $effect_name}})
    MERGE (cause)-[r:CAUSES {{weight: $weight}}]->(effect)
    RETURN r
    """
    
    # يجب التأكد من تمرير المعلمات بشكل آمن لتجنب حقن Cypher
    parameters = {
        "cause_name": cause_name,
        "effect_name": effect_name,
        "weight": initial_weight
    }
    
    # يجب استبدال {cause_type} و {effect_type} مباشرة في النص لتجنب قيود Cypher على أنواع العقد
    formatted_query = query.format(cause_type=cause_type, effect_type=effect_type)
    
    # تنفيذ الاستعلام
    # handler.execute_query(formatted_query, parameters)
    print(f"تم إنشاء الرابط: {cause_name} ({initial_weight}) -> {effect_name}")
    
# مثال للاستخدام (كود وهمي):
# create_causal_link("ارتفاع درجة الحرارة", "State", "انهيار الخادم", "State", 0.9)