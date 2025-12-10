import unittest
from unittest.mock import MagicMock, patch
from core.weights import update_system_confidence, LEARNING_RATE_ETA

# 1. إعداد بيانات وهمية لاستجابة Neo4j (قراءة مستوى الثقة الحالي)
MOCK_INITIAL_CONFIDENCE = [{"level": 0.80}]
MOCK_FALLBACK_CONFIDENCE = [] # استجابة فارغة (يجب أن يعود النظام إلى 0.5)

# ----------------------------------------------------------------------
# 2. فئة الاختبار
# ----------------------------------------------------------------------

class TestWeightFunctions(unittest.TestCase):
    
    def setUp(self):
        """إعداد كائن المعالج الوهمي قبل كل اختبار"""
        self.mock_handler = MagicMock()
        self.eta = LEARNING_RATE_ETA # 0.1
        
    # دالة مساعدة للتحقق من وسيط الكتابة الممرر
    def _assert_write_call(self, expected_confidence):
        """تتحقق من أن استدعاء الكتابة الأخير مرر قيمة الثقة الجديدة الصحيحة."""
        # الوصول إلى الوسيط الموضعي الثاني (args[1]) وهو قاموس 'parameters'
        write_call_parameters = self.mock_handler.execute_query.call_args_list[-1].args[1]
        self.assertAlmostEqual(write_call_parameters['new_level'], expected_confidence, places=4)
    
    # =========================================================
    # 1. اختبار سيناريوهات النجاح والفشل العادية (Normal Update)
    # =========================================================

    def test_01_successful_update_increases_confidence(self):
        """يجب أن يرتفع مستوى الثقة عند النجاح."""
        
        # 1. تهيئة الـ Mock للقراءة والكتابة
        self.mock_handler.execute_query.side_effect = [
            MOCK_INITIAL_CONFIDENCE, # القراءة الأولى
            None                     # الكتابة الثانية
        ]
        
        # 2. الاستدعاء: w(t+1) = 0.80 + 0.1 * 0.1 = 0.81
        new_confidence = update_system_confidence(self.mock_handler, success_delta=0.1, eta=self.eta)
        
        expected_confidence = 0.81
        self.assertAlmostEqual(new_confidence, expected_confidence, places=4)
        
        # 3. التحقق من استدعاء الكتابة (تم استخدام الدالة المساعدة)
        self.mock_handler.execute_query.assert_called()
        self._assert_write_call(expected_confidence)


    def test_02_failure_update_decreases_confidence(self):
        """يجب أن ينخفض مستوى الثقة عند الفشل (اكتشاف الهلوسة)."""
        
        # 1. تهيئة الـ Mock للقراءة والكتابة
        self.mock_handler.execute_query.side_effect = [
            MOCK_INITIAL_CONFIDENCE, # القراءة الأولى
            None
        ]
        
        # 2. الاستدعاء: w(t+1) = 0.80 + 0.1 * (-0.2) = 0.78
        new_confidence = update_system_confidence(self.mock_handler, success_delta=-0.2, eta=self.eta)
        
        expected_confidence = 0.78
        self.assertAlmostEqual(new_confidence, expected_confidence, places=4)
        
        # 3. التحقق من استدعاء الكتابة
        self._assert_write_call(expected_confidence)
    
    
    # =========================================================
    # 2. اختبار دالة القص (Clipping Function)
    # =========================================================

    def test_03_clipping_prevents_going_above_one(self):
        """يجب أن يتم قص الوزن عند 1.0 (الحد الأقصى)."""
        
        # 1. تهيئة الـ Mock للقراءة والكتابة
        self.mock_handler.execute_query.side_effect = [
            [{"level": 0.95}], # القراءة الأولى: 0.95
            None
        ]
        
        # 2. الاستدعاء: w(t+1) = 0.95 + 0.1 * 0.6 = 1.01 --> يقص إلى 1.0
        new_confidence = update_system_confidence(self.mock_handler, success_delta=0.6, eta=self.eta)
        
        expected_confidence = 1.0
        self.assertAlmostEqual(new_confidence, expected_confidence, places=4)
        
        # 3. التحقق من استدعاء الكتابة
        self._assert_write_call(expected_confidence)

    def test_04_clipping_prevents_going_below_zero(self):
        """يجب أن يتم قص الوزن عند 0.0 (الحد الأدنى)."""
        
        # 1. تهيئة الـ Mock للقراءة والكتابة
        self.mock_handler.execute_query.side_effect = [
            [{"level": 0.05}], # القراءة الأولى: 0.05
            None
        ]
        
        # 2. الاستدعاء: w(t+1) = 0.05 + 0.1 * (-0.6) = -0.01 --> يقص إلى 0.0
        new_confidence = update_system_confidence(self.mock_handler, success_delta=-0.6, eta=self.eta)
        
        expected_confidence = 0.0
        self.assertAlmostEqual(new_confidence, expected_confidence, places=4)
        
        # 3. التحقق من استدعاء الكتابة
        self._assert_write_call(expected_confidence)

    # =========================================================
    # 3. اختبار سيناريو القيمة الافتراضية
    # =========================================================

    def test_05_default_value_on_read_failure(self):
        """يجب أن يستخدم النظام 0.5 إذا فشل في قراءة المستوى الحالي."""
        
        # 1. تهيئة الـ Mock للقراءة والكتابة (فشل في القراءة الأولى)
        self.mock_handler.execute_query.side_effect = [
            MOCK_FALLBACK_CONFIDENCE, # القراءة الأولى: []
            None
        ]
        
        # 2. الاستدعاء: w(t+1) = 0.5 (افتراضي) + 0.1 * 0.5 = 0.55
        new_confidence = update_system_confidence(self.mock_handler, success_delta=0.5, eta=self.eta)
        
        expected_confidence = 0.55
        self.assertAlmostEqual(new_confidence, expected_confidence, places=4)
        
        # 3. التحقق من استدعاء الكتابة
        self._assert_write_call(expected_confidence)


if __name__ == '__main__':
    unittest.main()
