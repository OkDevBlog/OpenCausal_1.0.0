// OpenCausal - Seed Knowledge Script (Domain: Server Management & Performance)
// التاريخ: 2025-12-10

// ----------------------------------------------------------------------
// 1. إنشاء العقد الأساسية (Entities, States, Interventions)
// ----------------------------------------------------------------------

// الحالات (States)
MERGE (s1:State {name: 'High CPU Utilization'});
MERGE (s2:State {name: 'High Latency'});
MERGE (s3:State {name: 'Server Crash'});
MERGE (s4:State {name: 'Memory Leak'});
MERGE (s5:State {name: 'Database Query Slowdown'});
MERGE (s6:State {name: 'Service Degradation'});

// الإجراءات (Interventions)
MERGE (i1:Intervention {name: 'Restart Application Service'});
MERGE (i2:Intervention {name: 'Increase RAM Allocation'});
MERGE (i3:Intervention {name: 'Optimize Database Index'});

// الكيانات (Entities)
MERGE (e1:Entity {name: 'Logging Module'});
MERGE (e2:Entity {name: 'Web Server Process'});


// ----------------------------------------------------------------------
// 2. إنشاء الروابط السببية الموزونة (CAUSES Edges)
// ----------------------------------------------------------------------

// أ. روابط قوية (w ~ 0.9): حقائق موثوقة
// الذاكرة المتسربة تسبب استهلاك وحدة المعالجة المركزية
MERGE (s4)-[:CAUSES {weight: 0.9}]->(s1);
// استهلاك وحدة المعالجة المركزية يسبب انهيار الخادم
MERGE (s1)-[:CAUSES {weight: 0.95}]->(s3);
// تباطؤ الاستعلامات يسبب زمن استجابة عالٍ
MERGE (s5)-[:CAUSES {weight: 0.9}]->(s2);

// ب. روابط متوسطة (w ~ 0.7): قابلة للتعديل والتحقق
// عملية الخادم تتسبب في استهلاك وحدة المعالجة المركزية
MERGE (e2)-[:CAUSES {weight: 0.75}]->(s1);
// وحدة التسجيل تسبب تسرب الذاكرة
MERGE (e1)-[:CAUSES {weight: 0.7}]->(s4);

// ج. روابط التدخل (w ~ 0.8): نتائج الإجراءات
// إعادة تشغيل التطبيق تنهي عملية الخادم
MERGE (i1)-[:CAUSES {weight: 0.85}]->(e2_end:State {name: 'Server Process Ended'});
// تحسين الفهرس ينهي تباطؤ الاستعلام
MERGE (i3)-[:CAUSES {weight: 0.8}]->(s5_end:State {name: 'Query Latency Fixed'});
// زيادة الذاكرة توقف تسرب الذاكرة
MERGE (i2)-[:CAUSES {weight: 0.8}]->(s4_end:State {name: 'Memory Leak Contained'});

// ----------------------------------------------------------------------
// 3. روابط غير موثوقة أو زائفة (W ~ 0.2) - للتدريب على الرفض
// ----------------------------------------------------------------------

// هذا رابط زائفة: بطء الشبكة يسبب انهيار الخادم (عادة غير صحيح مباشرة)
MERGE (s_net:State {name: 'Network Slowdown'});
MERGE (s_net)-[:CAUSES {weight: 0.2}]->(s3);

// ----------------------------------------------------------------------
// 4. إضافة الوعي الذاتي: عقدة ثقة النظام (Self-Confidence Node)
// ----------------------------------------------------------------------

// يتم إنشاء العقدة وتعيين القيمة الأولية في خطوة واحدة لضمان تعريف sc
MERGE (sc:SelfAwareness {name: 'System_Confidence'})
// إعطاء النظام ثقة أولية عالية نسبياً (0.9)
SET sc.current_level = 0.9; 

// ربط عقدة الثقة بالكيانات الرئيسية (يتطلب MATCH جديدًا بعد المعاملة السابقة)
MATCH (sc:SelfAwareness {name: 'System_Confidence'}), (i3:Intervention {name: 'Optimize Database Index'})
MERGE (sc)-[:TRUSTS_PROCEDURE {weight: 0.9}]->(i3);

// ----------------------------------------------------------------------
// 5. مسار الابتكار (للسيناريو 3)
// ----------------------------------------------------------------------

// إضافة عقدة User Frustration (الهدف النهائي)
MERGE (s7:State {name: 'User Frustration'}); 

// ⭐⭐ التصحيح هنا: نستخدم MATCH لتحديد العقد الموجودة، ثم ننشئ العلاقة ⭐⭐
MATCH (s2:State {name: 'High Latency'}), (s7:State {name: 'User Frustration'})
MERGE (s2)-[:CAUSES {weight: 0.6, constraint: 'High_Cost'}]->(s7);