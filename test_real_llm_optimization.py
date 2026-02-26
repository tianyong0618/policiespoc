#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试真实LLM调用的性能优化效果
"""

import time
import json
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - TestRealLLM - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
import sys
import os
sys.path.insert(0, os.path.abspath('code'))

from langchain.presentation.orchestrator import Orchestrator

class TestRealLLMOptimization:
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
    
    def run_test(self):
        """运行测试"""
        logger.info("开始运行真实LLM性能优化效果测试")
        
        # 测试用例
        test_case = {
            "input": "我熟悉直播带货和网店运营，有场地补贴落地经验，想从事电商创业相关工作。",
            "name": "电商创业相关工作查询"
        }
        
        # 运行测试
        execution_time = self.test_user_query(test_case["input"], test_case["name"])
        
        # 测试缓存效果
        logger.info("测试缓存效果")
        cache_execution_time = self.test_user_query(test_case["input"], f"{test_case['name']}（缓存测试）")
        
        # 打印测试结果
        logger.info("测试结果汇总")
        logger.info("=" * 80)
        logger.info(f"首次查询耗时: {execution_time:.2f}秒")
        logger.info(f"缓存查询耗时: {cache_execution_time:.2f}秒")
        
        # 检查是否达到优化目标
        if execution_time < 5:
            logger.info("✅ 优化目标达成：首次查询响应时间小于5秒")
        else:
            logger.info("❌ 优化目标未达成：首次查询响应时间大于5秒")
        
        if cache_execution_time < 1:
            logger.info("✅ 缓存优化目标达成：缓存查询响应时间小于1秒")
        else:
            logger.info("❌ 缓存优化目标未达成：缓存查询响应时间大于1秒")
        
        return execution_time, cache_execution_time

if __name__ == "__main__":
    test = TestRealLLMOptimization()
    test.run_test()
