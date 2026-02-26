#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试性能优化效果
"""

import time
import json
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - TestOptimization - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
import sys
import os
sys.path.insert(0, os.path.abspath('code'))

from langchain.presentation.orchestrator import Orchestrator

class TestOptimizationEffect:
    def __init__(self):
        """初始化测试"""
        self.orchestrator = Orchestrator()
    
    def test_user_query(self, user_input, test_name):
        """测试用户查询"""
        logger.info(f"开始测试: {test_name}")
        logger.info(f"用户输入: {user_input}")
        
        # 记录开始时间
        start_time = time.time()
        
        # 执行查询
        result = self.orchestrator.process_query(user_input)
        
        # 记录结束时间
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 打印结果
        logger.info(f"测试完成，耗时: {execution_time:.2f}秒")
        logger.info(f"执行时间: {result.get('execution_time', execution_time):.2f}秒")
        logger.info(f"缓存命中率: {result.get('from_cache', False)}")
        
        # 打印响应内容
        response = result.get('response', {})
        logger.info(f"肯定部分: {response.get('positive', '')[:100]}...")
        logger.info(f"否定部分: {response.get('negative', '')[:100]}...")
        logger.info(f"主动建议: {response.get('suggestions', '')[:100]}...")
        
        return execution_time
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("开始运行性能优化效果测试")
        
        # 测试用例
        test_cases = [
            {
                "input": "我熟悉直播带货和网店运营，有场地补贴落地经验，想从事电商创业相关工作。",
                "name": "电商创业相关工作查询"
            },
            {
                "input": "我有中级电工证，想了解技能补贴政策",
                "name": "技能补贴政策查询"
            },
            {
                "input": "我想找一份兼职工作",
                "name": "兼职工作查询"
            },
            {
                "input": "我是一名失业人员，有什么政策可以申请",
                "name": "失业人员政策查询"
            }
        ]
        
        # 运行测试
        results = []
        for test_case in test_cases:
            execution_time = self.test_user_query(test_case["input"], test_case["name"])
            results.append({
                "test_name": test_case["name"],
                "input": test_case["input"],
                "execution_time": execution_time
            })
            logger.info("=" * 80)
        
        # 测试缓存效果
        logger.info("测试缓存效果")
        for test_case in test_cases[:1]:  # 只测试第一个用例的缓存效果
            execution_time = self.test_user_query(test_case["input"], f"{test_case['name']}（缓存测试）")
            results.append({
                "test_name": f"{test_case['name']}（缓存测试）",
                "input": test_case["input"],
                "execution_time": execution_time
            })
            logger.info("=" * 80)
        
        # 打印测试结果
        logger.info("测试结果汇总")
        logger.info("=" * 80)
        for result in results:
            logger.info(f"{result['test_name']}: {result['execution_time']:.2f}秒")
        
        # 计算平均响应时间
        average_time = sum(r["execution_time"] for r in results) / len(results)
        logger.info(f"平均响应时间: {average_time:.2f}秒")
        
        # 检查是否达到优化目标
        if average_time < 5:
            logger.info("✅ 优化目标达成：平均响应时间小于5秒")
        else:
            logger.info("❌ 优化目标未达成：平均响应时间大于5秒")
        
        return results

if __name__ == "__main__":
    test = TestOptimizationEffect()
    test.run_all_tests()
