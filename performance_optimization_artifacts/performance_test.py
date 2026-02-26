import time
import asyncio
import json
import random
from concurrent.futures import ThreadPoolExecutor

# 模拟数据
def generate_mock_data():
    """生成模拟数据"""
    # 模拟政策数据
    mock_policies = [
        {
            "policy_id": f"POLICY_{i}",
            "title": f"政策{i}",
            "description": f"这是政策{i}的详细描述",
            "conditions": [f"条件{i}-{j}" for j in range(3)],
            "benefits": [f"福利{i}-{j}" for j in range(2)],
            "eligibility": f"适用条件{i}"
        }
        for i in range(100)
    ]
    
    # 模拟岗位数据
    mock_jobs = [
        {
            "job_id": f"JOB_{i}",
            "title": f"岗位{i}",
            "description": f"这是岗位{i}的详细描述",
            "requirements": [f"要求{i}-{j}" for j in range(3)],
            "salary": f"薪资{i}",
            "benefits": [f"福利{i}-{j}" for j in range(2)]
        }
        for i in range(50)
    ]
    
    # 模拟用户输入
    mock_user_inputs = [
        "我想了解失业补贴政策",
        "我有高级电工证，能申请什么补贴？",
        "我想找一份兼职工作",
        "我想了解职业技能提升相关政策",
        "我是一名应届毕业生，有什么就业政策？",
        "我想了解创业补贴政策",
        "我有中级焊工证，能申请什么技能补贴？",
        "我想了解灵活就业相关政策",
        "我想了解社保缴纳相关政策",
        "我想了解住房补贴政策"
    ]
    
    return mock_policies, mock_jobs, mock_user_inputs

# 测试缓存性能
class CacheTest:
    def __init__(self):
        self.mock_policies, self.mock_jobs, self.mock_user_inputs = generate_mock_data()
    
    def test_memory_cache(self):
        """测试内存缓存性能"""
        from code.langchain.infrastructure.cache_manager import CacheManager
        
        cache = CacheManager()
        start_time = time.time()
        
        # 测试缓存写入
        for i, policy in enumerate(self.mock_policies):
            cache.set(f"policy_{i}", policy)
        
        for i, job in enumerate(self.mock_jobs):
            cache.set(f"job_{i}", job)
        
        # 测试缓存读取
        for i in range(len(self.mock_policies)):
            cache.get(f"policy_{i}")
        
        for i in range(len(self.mock_jobs)):
            cache.get(f"job_{i}")
        
        end_time = time.time()
        return end_time - start_time
    
    def test_redis_cache(self):
        """测试Redis缓存性能"""
        try:
            import redis
            
            # 连接Redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            
            start_time = time.time()
            
            # 测试缓存写入
            for i, policy in enumerate(self.mock_policies):
                r.set(f"policy_{i}", json.dumps(policy))
            
            for i, job in enumerate(self.mock_jobs):
                r.set(f"job_{i}", json.dumps(job))
            
            # 测试缓存读取
            for i in range(len(self.mock_policies)):
                r.get(f"policy_{i}")
            
            for i in range(len(self.mock_jobs)):
                r.get(f"job_{i}")
            
            end_time = time.time()
            return end_time - start_time
        except Exception as e:
            print(f"Redis测试失败: {e}")
            return float('inf')

# 测试异步性能
class AsyncTest:
    def __init__(self):
        self.mock_policies, self.mock_jobs, self.mock_user_inputs = generate_mock_data()
    
    def sync_task(self, task_id):
        """同步任务"""
        # 模拟IO操作
        time.sleep(0.01)
        return f"Task {task_id} completed"
    
    async def async_task(self, task_id):
        """异步任务"""
        # 模拟IO操作
        await asyncio.sleep(0.01)
        return f"Task {task_id} completed"
    
    def test_sync_performance(self):
        """测试同步性能"""
        start_time = time.time()
        
        # 运行100个同步任务
        results = []
        for i in range(100):
            results.append(self.sync_task(i))
        
        end_time = time.time()
        return end_time - start_time
    
    def test_async_performance(self):
        """测试异步性能"""
        async def run_tasks():
            tasks = []
            for i in range(100):
                tasks.append(self.async_task(i))
            await asyncio.gather(*tasks)
        
        start_time = time.time()
        asyncio.run(run_tasks())
        end_time = time.time()
        return end_time - start_time
    
    def test_asyncio_with_uvloop(self):
        """测试使用uvloop的异步性能"""
        try:
            import uvloop
            uvloop.install()
            
            async def run_tasks():
                tasks = []
                for i in range(100):
                    tasks.append(self.async_task(i))
                await asyncio.gather(*tasks)
            
            start_time = time.time()
            asyncio.run(run_tasks())
            end_time = time.time()
            return end_time - start_time
        except Exception as e:
            print(f"uvloop测试失败: {e}")
            return float('inf')

# 测试HTTP客户端性能
class HTTPClientTest:
    def __init__(self):
        # 模拟HTTP请求
        self.mock_urls = [f"http://example.com/api/{i}" for i in range(100)]
    
    def test_requests(self):
        """测试requests库性能"""
        try:
            import requests
            
            # 模拟响应
            class MockResponse:
                def __init__(self, json_data, status_code):
                    self.json_data = json_data
                    self.status_code = status_code
                
                def json(self):
                    return self.json_data
            
            # 模拟get方法
            original_get = requests.get
            def mock_get(url, *args, **kwargs):
                time.sleep(0.01)
                return MockResponse({"data": "mock data", "url": url}, 200)
            
            requests.get = mock_get
            
            start_time = time.time()
            
            # 运行100个HTTP请求
            results = []
            for url in self.mock_urls:
                results.append(requests.get(url).json())
            
            end_time = time.time()
            requests.get = original_get
            return end_time - start_time
        except Exception as e:
            print(f"requests测试失败: {e}")
            return float('inf')
    
    def test_httpx_sync(self):
        """测试httpx同步性能"""
        try:
            import httpx
            
            start_time = time.time()
            
            # 运行100个HTTP请求
            results = []
            with httpx.Client() as client:
                for url in self.mock_urls:
                    # 模拟响应
                    time.sleep(0.01)
                    results.append({"data": "mock data", "url": url})
            
            end_time = time.time()
            return end_time - start_time
        except Exception as e:
            print(f"httpx同步测试失败: {e}")
            return float('inf')
    
    def test_httpx_async(self):
        """测试httpx异步性能"""
        try:
            import httpx
            
            async def run_requests():
                results = []
                async with httpx.AsyncClient() as client:
                    tasks = []
                    for url in self.mock_urls:
                        # 模拟响应
                        task = asyncio.create_task(asyncio.sleep(0.01))
                        tasks.append(task)
                    await asyncio.gather(*tasks)
                    for url in self.mock_urls:
                        results.append({"data": "mock data", "url": url})
                return results
            
            start_time = time.time()
            asyncio.run(run_requests())
            end_time = time.time()
            return end_time - start_time
        except Exception as e:
            print(f"httpx异步测试失败: {e}")
            return float('inf')

# 运行所有测试
def run_all_tests():
    """运行所有性能测试"""
    results = {}
    
    # 测试缓存性能
    print("测试缓存性能...")
    cache_test = CacheTest()
    memory_cache_time = cache_test.test_memory_cache()
    redis_cache_time = cache_test.test_redis_cache()
    
    results['cache'] = {
        'memory_cache': memory_cache_time,
        'redis_cache': redis_cache_time,
        'improvement': (memory_cache_time - redis_cache_time) / memory_cache_time * 100 if memory_cache_time > 0 else 0
    }
    
    # 测试异步性能
    print("测试异步性能...")
    async_test = AsyncTest()
    sync_time = async_test.test_sync_performance()
    async_time = async_test.test_async_performance()
    uvloop_time = async_test.test_asyncio_with_uvloop()
    
    results['async'] = {
        'sync': sync_time,
        'asyncio': async_time,
        'uvloop': uvloop_time,
        'async_improvement': (sync_time - async_time) / sync_time * 100 if sync_time > 0 else 0,
        'uvloop_improvement': (async_time - uvloop_time) / async_time * 100 if async_time > 0 else 0
    }
    
    # 测试HTTP客户端性能
    print("测试HTTP客户端性能...")
    http_test = HTTPClientTest()
    requests_time = http_test.test_requests()
    httpx_sync_time = http_test.test_httpx_sync()
    httpx_async_time = http_test.test_httpx_async()
    
    results['http'] = {
        'requests': requests_time,
        'httpx_sync': httpx_sync_time,
        'httpx_async': httpx_async_time,
        'httpx_sync_improvement': (requests_time - httpx_sync_time) / requests_time * 100 if requests_time > 0 else 0,
        'httpx_async_improvement': (requests_time - httpx_async_time) / requests_time * 100 if requests_time > 0 else 0
    }
    
    # 打印结果
    print("\n性能测试结果:")
    print("=" * 60)
    
    # 缓存测试结果
    print("\n缓存性能测试:")
    print(f"内存缓存时间: {memory_cache_time:.4f}秒")
    print(f"Redis缓存时间: {redis_cache_time:.4f}秒")
    print(f"性能提升: {results['cache']['improvement']:.2f}%")
    
    # 异步测试结果
    print("\n异步性能测试:")
    print(f"同步时间: {sync_time:.4f}秒")
    print(f"asyncio时间: {async_time:.4f}秒")
    print(f"uvloop时间: {uvloop_time:.4f}秒")
    print(f"asyncio提升: {results['async']['async_improvement']:.2f}%")
    print(f"uvloop提升: {results['async']['uvloop_improvement']:.2f}%")
    
    # HTTP客户端测试结果
    print("\nHTTP客户端性能测试:")
    print(f"requests时间: {requests_time:.4f}秒")
    print(f"httpx同步时间: {httpx_sync_time:.4f}秒")
    print(f"httpx异步时间: {httpx_async_time:.4f}秒")
    print(f"httpx同步提升: {results['http']['httpx_sync_improvement']:.2f}%")
    print(f"httpx异步提升: {results['http']['httpx_async_improvement']:.2f}%")
    
    # 保存结果
    with open('performance_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("\n测试结果已保存到 performance_test_results.json")
    
    return results

if __name__ == "__main__":
    run_all_tests()
