import unittest
from unittest.mock import MagicMock, patch
from core.verify_causal import verify_causal_path, TRUST_THRESHOLD
from core.weights import update_causal_weight
from core.bridge import process_and_learn

# ----------------------------------------------------------------------
# 1. إعداد البيانات الوهمية (Mock Data)
# ----------------------------------------------------------------------

SUCCESS_PATH_RESPONSE = [
    {
        "path_weight": 0.855,  
        "path_details": [
            {"start": "Memory Leak", "end": "High CPU Utilization", "weight": 0.9},
            {"start": "High CPU Utilization", "end": "Server Crash", "weight": 0.95}
        ]
    }
]

FAILURE_PATH_RESPONSE = [] 

# ----------------------------------------------------------------------
# 2. فئة الاختبار
# ----------------------------------------------------------------------

class TestCausalBridge(unittest.TestCase):
    
    def setUp(self):
        """إعدادات قبل كل اختبار"""
        self.mock_handler = MagicMock()
        self.mock_llm_client = MagicMock()
        
    # =========================================================
    # 3. اختبار وظيفة التحقق (Verification Test)
    # =========================================================

    def test_01_verify_successful_path(self):
        """يجب أن ينجح التحقق في مسار ذي وزن عالٍ."""
        
        self.mock_handler.execute_query.return_value = SUCCESS_PATH_RESPONSE
        
        result = verify_causal_path(self.mock_handler, "Memory Leak", "Server Crash", TRUST_THRESHOLD)
        
        self.assertIsNotNone(result)
        self.assertGreater(result['path_weight'], TRUST_THRESHOLD)

    def test_02_verify_hallucination_failure(self):
        """يجب أن يفشل التحقق عند عدم وجود مسار قوي (منع الهلوسة)."""
        
        self.mock_handler.execute_query.return_value = FAILURE_PATH_RESPONSE 
        
        result = verify_causal_path(self.mock_handler, "Network Slowdown", "Server Crash", TRUST_THRESHOLD)
        
        self.assertIsNone(result)

    # =========================================================
    # 4. اختبار التعلم اللحظي (Inference-Time Learning Test)
    # =========================================================

    def test_03_weight_update_on_success(self):
        """يجب أن يتم استدعاء تحديث الوزن عند النجاح."""
        
        self.mock_handler.execute_query.reset_mock()
        
        update_causal_weight(self.mock_handler, SUCCESS_PATH_RESPONSE[0]['path_details'], success_delta=1.0)
        
        self.assertEqual(self.mock_handler.execute_query.call_count, 2) 
        
        # --------------------------------------------------------------------------------------------------
        # ⭐ التعديل هنا: الوصول إلى قاموس parameters كـ وسيط موضعي (args[1])
        # --------------------------------------------------------------------------------------------------
        # call_args_list[-1] هو القاموس الذي يحتوي على (args, kwargs) لآخر استدعاء
        # args[1] هي الوسيط الموضعي الثاني، وهو قاموس 'parameters'
        last_call_parameters = self.mock_handler.execute_query.call_args_list[-1].args[1]
        
        self.assertEqual(last_call_parameters['new_weight'], 1.0) # تحقق من المفتاح داخل قاموس parameters

    # =========================================================
    # 5. اختبار آلية التعلم النشط (Active Learning Test)
    # =========================================================
    
    # يجب استخدام @patch للدوال الخارجية مثل LLM و verify_causal_path
    @patch('core.bridge.verify_causal_path', return_value=None) 
    @patch('core.bridge.generate_exploratory_question', return_value="ما هي الخطوة المفقودة في البروتوكول XYZ؟")
    @patch('core.bridge.extract_causal_claims_from_llm', return_value=[{"cause": "A", "effect": "B", "claim_type": "CAUSES"}])
    def test_04_active_learning_on_gap(self, mock_extract, mock_generate, mock_verify):
        """عند فشل التحقق، يجب تفعيل آلية التعلم النشط."""
        
        result = process_and_learn("نص يقترح علاقة غير مؤكدة", self.mock_handler, self.mock_llm_client)
        
        self.assertEqual(result['status'], "Failure - Causal Gap Found (Active Learning)")
        mock_generate.assert_called_once()
        self.assertIn("المفقودة", result['question'])

if __name__ == '__main__':
    unittest.main()
