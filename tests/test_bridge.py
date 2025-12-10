import unittest
from unittest.mock import MagicMock, patch
from core.verify_causal import verify_causal_path, TRUST_THRESHOLD
from core.weights import update_causal_weight
from core.bridge import process_and_learn, attempt_innovative_solution

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

# ... (بعد تعريف FAILURE_PATH_RESPONSE)

# بيانات وهمية للمسار الابتكاري
INNOVATIVE_PATH_RESPONSE = {
    "path_weight": 0.95,
    "path_details": [
        {"start": "Memory Leak", "end": "Fast Patch", "weight": 0.95},
        {"start": "Fast Patch", "end": "Server Crash", "weight": 0.95}
    ]
}

# بيانات وهمية لتقييم المخاطر (مخاطر منخفضة < 0.7)
LOW_RISK_ASSESSMENT_RESPONSE = {
    "risk_score": 0.3,
    "side_effects": "Minor performance degradation during initial deployment."
}

# بيانات وهمية لتقييم المخاطر (مخاطر عالية > 0.7)
HIGH_RISK_ASSESSMENT_RESPONSE = {
    "risk_score": 0.85, 
    "side_effects": "High probability of data corruption due to bypassing security check."
}

# ----------------------------------------------------------------------
# 2. فئة الاختبار (TestCausalBridge)
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

    # =========================================================
    # 5. اختبار الابتكار وتحليل المخاطر (Innovation and Risk Test)
    # =========================================================
    
    @patch('core.bridge.find_innovative_path')
    @patch('core.bridge.assess_innovative_risk')
    def test_05_innovative_solution_low_risk(self, mock_assess_risk, mock_find_path):
        """يجب أن يقبل النظام الحل الابتكاري إذا كانت مخاطره منخفضة."""
        
        # 1. إعداد محاكاة لإيجاد المسار بنجاح
        mock_find_path.return_value = INNOVATIVE_PATH_RESPONSE
        
        # 2. إعداد محاكاة لتقييم المخاطر (مخاطر منخفضة < 0.7)
        mock_assess_risk.return_value = LOW_RISK_ASSESSMENT_RESPONSE
        
        result = attempt_innovative_solution(self.mock_handler, self.mock_llm_client, "Memory Leak", "Server Crash")
        
        self.assertEqual(result['status'], "Innovative Solution Found")
        self.assertLess(result['risk_assessment']['risk_score'], 0.7)
        mock_assess_risk.assert_called_once()
        mock_find_path.assert_called_once()


    @patch('core.bridge.find_innovative_path')
    @patch('core.bridge.assess_innovative_risk')
    def test_06_innovative_solution_high_risk(self, mock_assess_risk, mock_find_path):
        """يجب أن يرفض النظام الحل الابتكاري إذا كانت مخاطره عالية (> 0.7)."""
        
        # 1. إعداد محاكاة لإيجاد المسار بنجاح
        mock_find_path.return_value = INNOVATIVE_PATH_RESPONSE
        
        # 2. إعداد محاكاة لتقييم المخاطر (مخاطر عالية > 0.7)
        mock_assess_risk.return_value = HIGH_RISK_ASSESSMENT_RESPONSE
        
        result = attempt_innovative_solution(self.mock_handler, self.mock_llm_client, "Memory Leak", "Server Crash")
        
        self.assertEqual(result['status'], "Innovative Solution REJECTED")
        self.assertIn("ارتفاع المخاطر", result['message'])
        mock_assess_risk.assert_called_once()
        mock_find_path.assert_called_once()

if __name__ == '__main__':
    unittest.main()
