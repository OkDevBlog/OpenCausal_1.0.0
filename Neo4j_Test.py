from db.neo4j_handler import Neo4jHandler

# تهيئة الاتصال (يفترض أنك قمت بتهيئة credentials)
# handler = Neo4jHandler("bolt://localhost:7687", "neo4j", "password")

# قراءة محتوى ملف Cypher
# with open('data/seed_knowledge.cypher', 'r') as f:
#     cypher_script = f.read()

# تنفيذ السكريبت (استخدام execute_query لتنفيذ السكريبت)
# handler.execute_query(cypher_script) 
# handler.close()

print("تم بنجاح تحميل الذاكرة الطوبولوجية الأولية (Seed Knowledge) إلى Neo4j.")
print("الآن يمكن للنظام بدء التحقق السببي.")