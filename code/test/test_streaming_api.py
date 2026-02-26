import json
import time
import unittest
import sys
import os
from unittest.mock import Mock, MagicMock
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入要测试的模块
from langchain.presentation.orchestrator.stream_processor import StreamProcessor


class MockOrchestrator:
    """模拟Orchestrator类"""
    def __init__(self):
        # 模拟意图识别器
        self.intent_recognizer = Mock()
        self.intent_recognizer.ir_identify_intent = Mock(return_value={
            "result": {
                "intent": "政策咨询",
                "entities": [
                    {"type": "skill", "value": "电工"},
                    {"type": "certificate", "value": "高级电工证"}
                ],
                "needs_job_recommendation": True,
                "needs_policy_recommendation": True
            }
        })
        
        # 模拟政策检索器
        self.policy_retriever = Mock()
        self.policy_retriever.pr_analyze_input = Mock(return_value={
            "needs_more_info": False
        })
        self.policy_retriever.pr_process_query = Mock(return_value={
            "relevant_policies": [
                {
                    "policy_id": "POLICY_A01",
                    "title": "技能提升补贴政策",
                    "content": "对取得高级职业资格证书的人员给予补贴",
                    "eligibility": "具有高级职业资格证书"
                },
                {
                    "policy_id": "POLICY_A02",
                    "title": "就业促进政策",
                    "content": "鼓励企业吸纳技能人才",
                    "eligibility": "企业吸纳技能人才"
                }
            ],
            "recommended_jobs": [
                {
                    "job_id": "JOB_A01",
                    "title": "高级电工",
                    "requirements": ["高级电工证", "3年以上经验"],
                    "features": "技能补贴",
                    "policy_relations": ["POLICY_A01"]
                },
                {
                    "job_id": "JOB_A02",
                    "title": "电工技师",
                    "requirements": ["中级电工证", "5年以上经验"],
                    "features": "技能补贴",
                    "policy_relations": ["POLICY_A02"]
                }
            ]
        })
        
        # 模拟响应生成器
        self.response_generator = Mock()
        self.response_generator.rg_generate_response = Mock(return_value={
            "positive": "您符合技能提升补贴政策的申请条件",
            "negative": "暂无不符合的政策",
            "suggestions": ["建议尽快申请技能补贴", "可以考虑报考更高级别的职业资格"]
        })


class TestStreamingAPI(unittest.TestCase):
    """测试流式API的性能和流畅度"""
    
    def setUp(self):
        """设置测试环境"""
        self.mock_orchestrator = MockOrchestrator()
        self.stream_processor = StreamProcessor(self.mock_orchestrator)
    
    def test_streaming_basic(self):
        """测试基本的流式处理功能"""
        user_input = "我有高级电工证，想了解相关政策和岗位"
        
        # 收集流式输出
        chunks = []
        start_time = time.time()
        
        for chunk in self.stream_processor.process_stream_query(user_input):
            chunks.append(chunk)
            # 模拟流式接收延迟
            time.sleep(0.01)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"基本流式测试完成，耗时: {processing_time:.3f}秒")
        print(f"生成的chunks数量: {len(chunks)}")
        
        # 验证结果
        self.assertGreater(len(chunks), 0, "应该有流式输出")
        
        # 验证每个chunk都是有效的JSON
        for i, chunk in enumerate(chunks):
            try:
                data = json.loads(chunk)
                self.assertIn("type", data, f"Chunk {i} 缺少type字段")
                self.assertIn("content", data, f"Chunk {i} 缺少content字段")
            except json.JSONDecodeError:
                self.fail(f"Chunk {i} 不是有效的JSON: {chunk}")
    
    def test_streaming_performance(self):
        """测试流式API的性能"""
        user_input = "我有高级电工证，想了解相关政策和岗位"
        
        # 测试多次调用的性能
        test_count = 5
        total_time = 0
        all_chunks = []
        
        for i in range(test_count):
            chunks = []
            start_time = time.time()
            
            for chunk in self.stream_processor.process_stream_query(user_input):
                chunks.append(chunk)
            
            end_time = time.time()
            iteration_time = end_time - start_time
            total_time += iteration_time
            all_chunks.append(chunks)
            
            print(f"性能测试迭代 {i+1}/{test_count}，耗时: {iteration_time:.3f}秒")
        
        average_time = total_time / test_count
        print(f"平均处理时间: {average_time:.3f}秒")
        
        # 验证所有迭代的结果一致性
        self.assertTrue(all(len(chunks) == len(all_chunks[0]) for chunks in all_chunks), 
                       "所有迭代的chunk数量应该一致")
    
    def test_streaming_stability(self):
        """测试流式API的稳定性"""
        test_cases = [
            "我有高级电工证，想了解相关政策和岗位",
            "我想找电工相关的工作",
            "技能补贴怎么申请",
            "电工技师的薪资水平如何",
            "我只有中级电工证，能申请什么政策"
        ]
        
        successful_cases = 0
        error_cases = 0
        
        for test_input in test_cases:
            try:
                chunks = []
                start_time = time.time()
                
                for chunk in self.stream_processor.process_stream_query(test_input):
                    chunks.append(chunk)
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                print(f"稳定性测试 '{test_input[:20]}...' 完成，耗时: {processing_time:.3f}秒")
                successful_cases += 1
            except Exception as e:
                print(f"稳定性测试 '{test_input[:20]}...' 失败: {e}")
                error_cases += 1
        
        print(f"稳定性测试完成: {successful_cases}成功, {error_cases}失败")
        self.assertEqual(error_cases, 0, "所有测试用例都应该成功")
    
    def test_streaming_cache(self):
        """测试流式API的缓存功能"""
        user_input = "我有高级电工证，想了解相关政策和岗位"
        
        # 第一次调用（应该不使用缓存）
        start_time_1 = time.time()
        chunks_1 = list(self.stream_processor.process_stream_query(user_input))
        end_time_1 = time.time()
        time_1 = end_time_1 - start_time_1
        
        # 第二次调用（应该使用缓存）
        start_time_2 = time.time()
        chunks_2 = list(self.stream_processor.process_stream_query(user_input))
        end_time_2 = time.time()
        time_2 = end_time_2 - start_time_2
        
        print(f"缓存测试 - 第一次调用: {time_1:.3f}秒")
        print(f"缓存测试 - 第二次调用: {time_2:.3f}秒")
        
        # 验证两次调用的结果一致
        self.assertEqual(len(chunks_1), len(chunks_2), "缓存结果应该与原始结果一致")
        self.assertEqual(chunks_1, chunks_2, "缓存结果应该与原始结果一致")
        
        # 验证缓存调用更快
        self.assertLess(time_2, time_1, "缓存调用应该比非缓存调用更快")
    
    def test_streaming_out_of_scope(self):
        """测试超出服务范围的流式处理"""
        # 修改意图识别器返回超出范围的意图
        self.mock_orchestrator.intent_recognizer.ir_identify_intent = Mock(return_value={
            "result": {
                "intent": "聊天",
                "entities": [],
                "needs_job_recommendation": False,
                "needs_policy_recommendation": False
            }
        })
        
        user_input = "今天天气怎么样"
        chunks = []
        
        for chunk in self.stream_processor.process_stream_query(user_input):
            chunks.append(chunk)
        
        print(f"超出范围测试完成，生成的chunks数量: {len(chunks)}")
        self.assertGreater(len(chunks), 0, "应该有流式输出")
        
        # 验证包含超出范围的提示
        has_out_of_scope = any("超出了系统可提供的服务范围" in chunk for chunk in chunks)
        self.assertTrue(has_out_of_scope, "应该包含超出范围的提示")


class StreamingPerformanceTest:
    """流式性能测试"""
    
    def __init__(self, stream_processor):
        self.stream_processor = stream_processor
    
    def test_latency(self, user_inputs):
        """测试流式响应的延迟"""
        results = []
        
        for user_input in user_inputs:
            chunk_times = []
            start_time = time.time()
            first_chunk_time = None
            
            for i, chunk in enumerate(self.stream_processor.process_stream_query(user_input)):
                current_time = time.time()
                if i == 0:
                    first_chunk_time = current_time - start_time
                chunk_times.append(current_time - start_time)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            results.append({
                "input": user_input,
                "first_chunk_latency": first_chunk_time,
                "total_time": total_time,
                "chunk_count": len(chunk_times),
                "chunk_intervals": [chunk_times[i] - chunk_times[i-1] for i in range(1, len(chunk_times))] if len(chunk_times) > 1 else []
            })
        
        return results
    
    def test_throughput(self, user_input, iterations=10):
        """测试流式API的吞吐量"""
        total_time = 0
        total_chunks = 0
        
        for i in range(iterations):
            start_time = time.time()
            chunks = list(self.stream_processor.process_stream_query(user_input))
            end_time = time.time()
            
            total_time += end_time - start_time
            total_chunks += len(chunks)
        
        average_time_per_request = total_time / iterations
        average_chunks_per_request = total_chunks / iterations
        throughput = iterations / total_time  # 请求/秒
        
        return {
            "average_time_per_request": average_time_per_request,
            "average_chunks_per_request": average_chunks_per_request,
            "throughput": throughput,
            "total_iterations": iterations,
            "total_time": total_time
        }


def run_comprehensive_test():
    """运行综合测试"""
    print("开始流式API综合测试...")
    
    # 创建测试实例
    mock_orchestrator = MockOrchestrator()
    stream_processor = StreamProcessor(mock_orchestrator)
    
    # 运行单元测试
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    
    # 运行性能测试
    performance_test = StreamingPerformanceTest(stream_processor)
    
    # 测试延迟
    test_inputs = [
        "我有高级电工证，想了解相关政策和岗位",
        "我想找电工相关的工作",
        "技能补贴怎么申请"
    ]
    
    print("\n测试流式响应延迟...")
    latency_results = performance_test.test_latency(test_inputs)
    for result in latency_results:
        print(f"输入: '{result['input'][:20]}...'")
        print(f"  首chunk延迟: {result['first_chunk_latency']:.3f}秒")
        print(f"  总时间: {result['total_time']:.3f}秒")
        print(f"  Chunk数量: {result['chunk_count']}")
        if result['chunk_intervals']:
            avg_interval = sum(result['chunk_intervals']) / len(result['chunk_intervals'])
            print(f"  平均间隔: {avg_interval:.3f}秒")
    
    # 测试吞吐量
    print("\n测试流式API吞吐量...")
    throughput_result = performance_test.test_throughput("我有高级电工证，想了解相关政策和岗位", 20)
    print(f"平均请求时间: {throughput_result['average_time_per_request']:.3f}秒")
    print(f"平均Chunk数量: {throughput_result['average_chunks_per_request']}")
    print(f"吞吐量: {throughput_result['throughput']:.2f}请求/秒")
    print(f"总测试时间: {throughput_result['total_time']:.3f}秒")
    
    print("\n流式API综合测试完成！")


if __name__ == "__main__":
    run_comprehensive_test()
