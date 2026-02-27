#!/usr/bin/env python3
import time
import logging
import sys
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - TestOptimization - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.append('/Users/tianyong/Documents/works/workspace/hp/公司文档/AI调研/政策咨询POC/code')

class TestOptimizationEffect:
    def __init__(self):
        """初始化测试类"""
        self.llm_call_count = 0
        self.total_response_time = 0
        self.test_queries = [
            "请为一位32岁、失业、持有中级电工证的女性推荐工作，她关注补贴申领和灵活时间。",
            "我是去年从广东回来的农民工，想在家开个小加工厂（小微企业），听说有返乡创业补贴，能领2万吗？另外创业贷款怎么申请？"
        ]
    
    def test_intent_recognition(self):
        """测试意图识别优化效果"""
        logger.info("开始测试意图识别优化效果...")
        
        try:
            from langchain.business.intent_analyzer import IntentAnalyzer
            intent_analyzer = IntentAnalyzer()
            
            for query in self.test_queries:
                start_time = time.time()
                result = intent_analyzer.ir_identify_intent(query)
                end_time = time.time()
                response_time = end_time - start_time
                
                logger.info(f"查询: {query[:50]}...")
                logger.info(f"意图识别响应时间: {response_time:.4f}秒")
                logger.info(f"识别结果: {result['result']['intent']}")
                logger.info(f"需要岗位推荐: {result['result']['needs_job_recommendation']}")
                logger.info(f"需要政策推荐: {result['result']['needs_policy_recommendation']}")
                logger.info(f"提取的实体数量: {len(result['result']['entities'])}")
                logger.info("-")
                
                self.total_response_time += response_time
        except Exception as e:
            logger.error(f"测试意图识别失败: {e}")
    
    def test_response_generation(self):
        """测试响应生成优化效果"""
        logger.info("开始测试响应生成优化效果...")
        
        try:
            from langchain.business.response_generator import ResponseGenerator
            response_generator = ResponseGenerator()
            
            # 模拟政策数据
            mock_policies = [
                {
                    "policy_id": "POLICY_A01",
                    "title": "创业担保贷款贴息政策",
                    "category": "创业扶持",
                    "key_info": "最高贷50万、期限3年，LPR-150BP以上部分财政贴息"
                },
                {
                    "policy_id": "POLICY_A02",
                    "title": "职业技能提升补贴政策",
                    "category": "就业扶持",
                    "key_info": "取得职业资格证书，可申领技能提升补贴"
                }
            ]
            
            # 模拟岗位数据
            mock_jobs = [
                {
                    "job_id": "JOB_A02",
                    "title": "职业技能培训讲师",
                    "requirements": ["持有相关技能证书", "有教学经验优先"],
                    "features": "传授实操技能，兼职模式灵活"
                }
            ]
            
            for query in self.test_queries:
                start_time = time.time()
                result = response_generator.rg_generate_response(
                    query,
                    mock_policies,
                    "通用场景",
                    recommended_jobs=mock_jobs
                )
                end_time = time.time()
                response_time = end_time - start_time
                
                logger.info(f"查询: {query[:50]}...")
                logger.info(f"响应生成时间: {response_time:.4f}秒")
                logger.info(f"生成的回答: {result['positive'][:100]}...")
                logger.info(f"建议: {result['suggestions'][:100]}...")
                logger.info("-")
                
                self.total_response_time += response_time
        except Exception as e:
            logger.error(f"测试响应生成失败: {e}")
    
    def test_cache_effectiveness(self):
        """测试缓存机制效果"""
        logger.info("开始测试缓存机制效果...")
        
        try:
            from langchain.infrastructure.cache_manager import CacheManager
            cache_manager = CacheManager()
            
            # 测试缓存命中率
            test_query = "我有中级电工证，想了解技能补贴政策"
            
            # 第一次查询（应该不命中缓存）
            start_time = time.time()
            from langchain.business.intent_analyzer import IntentAnalyzer
            intent_analyzer = IntentAnalyzer()
            result1 = intent_analyzer.ir_identify_intent(test_query)
            end_time1 = time.time()
            time1 = end_time1 - start_time
            
            # 第二次查询（应该命中缓存）
            start_time = time.time()
            result2 = intent_analyzer.ir_identify_intent(test_query)
            end_time2 = time.time()
            time2 = end_time2 - start_time
            
            logger.info(f"第一次查询时间: {time1:.4f}秒")
            logger.info(f"第二次查询时间: {time2:.4f}秒")
            logger.info(f"缓存效果: 速度提升 {time1/time2:.2f}倍")
            
            # 测试缓存统计
            stats = cache_manager.get_cache_stats()
            logger.info(f"缓存统计: 命中次数={stats['hit_count']}, 未命中次数={stats['miss_count']}, 命中率={stats['hit_rate']:.2f}%")
        except Exception as e:
            logger.error(f"测试缓存机制失败: {e}")
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("开始运行优化效果测试...")
        
        # 运行各项测试
        self.test_intent_recognition()
        self.test_response_generation()
        self.test_cache_effectiveness()
        
        # 计算平均响应时间
        average_time = self.total_response_time / (len(self.test_queries) * 2)  # 每个查询测试两个步骤
        logger.info(f"\n测试总结:")
        logger.info(f"总响应时间: {self.total_response_time:.4f}秒")
        logger.info(f"平均响应时间: {average_time:.4f}秒")
        logger.info("优化效果测试完成！")

if __name__ == "__main__":
    # 运行测试
    tester = TestOptimizationEffect()
    tester.run_all_tests()
