import os
import sys

# 模拟服务的导入路径设置
print(f"Current directory: {os.getcwd()}")

# 计算base_dir，与服务中的计算方式相同
try:
    # 从服务脚本路径计算
    serve_code_path = os.path.join(os.getcwd(), 'code', 'serve_code')
    base_dir = os.path.dirname(os.path.dirname(serve_code_path))
    print(f"Base directory: {base_dir}")
    
    # 添加code目录到Python路径
    code_path = os.path.join(base_dir, 'code')
    print(f"Code path: {code_path}")
    print(f"Code path exists: {os.path.exists(code_path)}")
    
    # 检查code目录下的内容
    if os.path.exists(code_path):
        print(f"Contents of code directory: {os.listdir(code_path)}")
        langchain_path = os.path.join(code_path, 'langchain')
        if os.path.exists(langchain_path):
            print(f"Contents of langchain directory: {os.listdir(langchain_path)}")
    
    # 添加到Python路径
    sys.path.insert(0, code_path)
    print(f"Python path after insertion: {sys.path[:5]}")
    
    # 尝试导入langchain模块
    try:
        # 先清理可能的模块缓存
        for module in list(sys.modules.keys()):
            if module.startswith('langchain'):
                del sys.modules[module]
        
        from langchain.orchestrator import Orchestrator
        print("Successfully imported Orchestrator")
        
        # 检查模块路径
        import langchain
        print(f"Langchain module path: {os.path.dirname(langchain.__file__)}")
        
        # 检查job_matcher模块
        from langchain import job_matcher
        print(f"Job matcher module path: {os.path.dirname(job_matcher.__file__)}")
        
        # 检查修改是否生效
        print("\nChecking if modifications are present:")
        with open(os.path.join(langchain_path, 'job_matcher.py'), 'r', encoding='utf-8') as f:
            content = f.read()
            if 'has_fixed_time' in content:
                print("✓ has_fixed_time is present in job_matcher.py")
            else:
                print("✗ has_fixed_time is NOT present in job_matcher.py")
            
            if '固定时间' in content:
                print("✓ 固定时间 is present in job_matcher.py")
            else:
                print("✗ 固定时间 is NOT present in job_matcher.py")
        
    except ImportError as e:
        print(f"Import error: {e}")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
