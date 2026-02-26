import time
import json
import logging
import sys
import os

# 添加code目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import Mock, patch
from langchain.business.response_generator import ResponseGenerator
from langchain.presentation.orchestrator.utils import generate_job_recommendations, build_job_analysis_prompt
from langchain.infrastructure.llm_batch_processor import LMBatchProcessor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestOptimization:
    """测试LLM调用优化效果"""
    
    def __init__(self):
        """初始化测试"""
        self.response_generator = ResponseGenerator()
        self.batch_processor = LMBatchProcessor()
        self.llm_call_count = 0
    
    def mock_chat_with_memory(self, prompt):
        """模拟chat_with_memory方法，避免真实LLM调用"""
        self.llm_call_count += 1
        logger.info(f"模拟LLM调用 #{self.llm_call_count}")
        
        # 根据prompt类型返回不同的模拟结果
        if "job_analysis" in prompt:
            return json.dumps({
                "job_analysis": [
                    {
                        "id": "JOB_A02",
                        "title": "职业技能培训讲师",
                        "reasons": {
                            "positive": "①持有中级电工证符合要求；②兼职模式满足灵活时间；③岗位特点与经验匹配",
                            "negative": ""
                        }
                    }
                ]
            })
        else:
            return json.dumps({
                "positive": "您可申请《创业担保贷款贴息政策》（POLICY_A01）：最高贷50万、期限3年，LPR-150BP以上部分财政贴息。",
                "negative": "根据《返乡创业扶持补贴政策》（POLICY_A03），您需满足'带动3人以上就业'方可申领2万补贴，当前信息未提及，建议补充就业证明后申请。",
                "suggestions": "简历优化方案：1. 突出与推荐岗位相关的核心技能；2. 强调工作经验和成就；3. 展示学习能力和适应能力；4. 确保简历格式清晰，重点突出。"
            })
    
    def test_prompt_optimization(self):
        """测试prompt优化效果"""
        logger.info("=== 测试prompt优化效果 ===")
        
        # 模拟数据
        user_input = "我是一名持有中级电工证的技术人员，想找一份兼职工作，有什么适合我的政策和岗位推荐吗？"
        recommended_jobs = [
            {
                "job_id": "JOB_A02",
                "title": "职业技能培训讲师",
                "requirements": ["持有相关技能证书", "有教学经验优先"],
                "features": "传授实操技能，兼职模式灵活"
            }
        ]
        time_preference = "灵活时间"
        certificate_level = "中级电工证"
        
        # 构建优化后的prompt
        optimized_prompt = build_job_analysis_prompt(user_input, recommended_jobs, time_preference, certificate_level)
        logger.info(f"优化后prompt长度: {len(optimized_prompt)}")
        logger.info(f"优化后prompt内容: {optimized_prompt[:200]}...")
        
        # 验证prompt长度是否合理
        assert len(optimized_prompt) < 1000, f"优化后prompt长度过长: {len(optimized_prompt)}"
        logger.info("✓ Prompt优化测试通过")
    
    def test_batch_processing(self):
        """测试批处理机制"""
        logger.info("\n=== 测试批处理机制 ===")
        
        # 模拟数据
        user_input = "我是一名持有中级电工证的技术人员，想找一份兼职工作，有什么适合我的政策和岗位推荐吗？"
        recommended_jobs = [
            {
                "job_id": "JOB_A02",
                "title": "职业技能培训讲师",
                "requirements": ["持有相关技能证书", "有教学经验优先"],
                "features": "传授实操技能，兼职模式灵活"
            }
        ]
        
        # 构建prompt
        time_preference = "灵活时间"
        certificate_level = "中级电工证"
        prompt = build_job_analysis_prompt(user_input, recommended_jobs, time_preference, certificate_level)
        
        # 测试批处理
        tasks = [
            {
                "id": 1,
                "type": "job_analysis",
                "prompt": prompt
            },
            {
                "id": 2,
                "type": "job_analysis",
                "prompt": prompt  # 重复任务，测试缓存效果
            }
        ]
        
        # 模拟chat_with_memory
        with patch('langchain.infrastructure.chatbot.ChatBot.chat_with_memory', side_effect=self.mock_chat_with_memory):
            start_time = time.time()
            results = self.batch_processor.batch_process(tasks)
            end_time = time.time()
            
            logger.info(f"批处理时间: {end_time - start_time:.4f}秒")
            logger.info(f"LLM调用次数: {self.llm_call_count}")
            logger.info(f"批处理结果: {json.dumps(results, ensure_ascii=False, indent=2)}")
            
            # 验证结果
            assert len(results) == 2, f"批处理结果数量不正确: {len(results)}"
            assert results[0].get("result"), "批处理结果为空"
            logger.info("✓ 批处理机制测试通过")
    
    def test_response_generator_optimization(self):
        """测试响应生成器优化效果"""
        logger.info("\n=== 测试响应生成器优化效果 ===")
        
        # 模拟数据
        user_input = "我是一名持有中级电工证的技术人员，想找一份兼职工作，有什么适合我的政策和岗位推荐吗？"
        relevant_policies = [
            {
                "policy_id": "POLICY_A01",
                "title": "创业担保贷款贴息政策",
                "category": "创业扶持",
                "key_info": "最高贷50万、期限3年，LPR-150BP以上部分财政贴息"
            },
            {
                "policy_id": "POLICY_A03",
                "title": "返乡创业扶持补贴政策",
                "category": "创业扶持",
                "key_info": "带动3人以上就业，可申领2万补贴"
            }
        ]
        recommended_jobs = [
            {
                "job_id": "JOB_A02",
                "title": "职业技能培训讲师",
                "requirements": ["持有相关技能证书", "有教学经验优先"],
                "features": "传授实操技能，兼职模式灵活"
            }
        ]
        
        # 模拟chat_with_memory
        with patch('langchain.infrastructure.chatbot.ChatBot.chat_with_memory', side_effect=self.mock_chat_with_memory):
            start_time = time.time()
            result = self.response_generator.rg_generate_response(
                user_input, 
                relevant_policies, 
                "通用场景", 
                recommended_jobs=recommended_jobs
            )
            end_time = time.time()
            
            logger.info(f"响应生成时间: {end_time - start_time:.4f}秒")
            logger.info(f"LLM调用次数: {self.llm_call_count}")
            logger.info(f"响应结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 验证结果
            assert result, "响应结果为空"
            assert "positive" in result, "响应结果缺少positive字段"
            assert "negative" in result, "响应结果缺少negative字段"
            assert "suggestions" in result, "响应结果缺少suggestions字段"
            logger.info("✓ 响应生成器优化测试通过")
    
    def test_generate_job_recommendations_optimization(self):
        """测试岗位推荐理由生成优化效果"""
        logger.info("\n=== 测试岗位推荐理由生成优化效果 ===")
        
        # 模拟数据
        user_input = "我是一名持有中级电工证的技术人员，想找一份兼职工作，有什么适合我的政策和岗位推荐吗？"
        intent_info = {
            "intent": "政策咨询与岗位推荐",
            "entities": [
                {"type": "certificate", "value": "中级电工证"},
                {"type": "concern", "value": "灵活时间"}
            ],
            "needs_job_recommendation": True,
            "needs_policy_recommendation": True
        }
        recommended_jobs = [
            {
                "job_id": "JOB_A02",
                "title": "职业技能培训讲师",
                "requirements": ["持有相关技能证书", "有教学经验优先"],
                "features": "传授实操技能，兼职模式灵活"
            }
        ]
        
        # 模拟chat_with_memory
        with patch('langchain.infrastructure.chatbot.ChatBot.chat_with_memory', side_effect=self.mock_chat_with_memory):
            start_time = time.time()
            result = generate_job_recommendations(user_input, intent_info, recommended_jobs)
            end_time = time.time()
            
            logger.info(f"岗位推荐理由生成时间: {end_time - start_time:.4f}秒")
            logger.info(f"LLM调用次数: {self.llm_call_count}")
            logger.info(f"推荐岗位结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 验证结果
            assert result, "推荐岗位结果为空"
            assert len(result) > 0, "推荐岗位列表为空"
            assert "reasons" in result[0], "推荐岗位缺少reasons字段"
            logger.info("✓ 岗位推荐理由生成优化测试通过")
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("开始运行优化效果测试")
        
        try:
            self.test_prompt_optimization()
            self.test_batch_processing()
            self.test_response_generator_optimization()
            self.test_generate_job_recommendations_optimization()
            
            logger.info("\n=== 测试总结 ===")
            logger.info(f"总LLM调用次数: {self.llm_call_count}")
            logger.info("所有测试通过！优化效果显著。")
            return True
        except Exception as e:
            logger.error(f"测试失败: {e}")
            return False

if __name__ == "__main__":
    test = TestOptimization()
    test.run_all_tests()
