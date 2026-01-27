import json
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - CourseMatcher - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CourseMatcher:
    def __init__(self):
        # 加载并缓存课程数据
        self.courses = self.load_courses()
        logger.info(f"加载了 {len(self.courses)} 门课程")
    
    def load_courses(self):
        """加载课程数据"""
        course_file = os.path.join(os.path.dirname(__file__), 'data', 'courses.json')
        try:
            with open(course_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载课程数据失败: {e}")
            return []
    
    def get_all_courses(self):
        """获取所有课程"""
        return self.courses
    
    def get_course_by_id(self, course_id):
        """根据ID获取课程"""
        for course in self.courses:
            if course['course_id'] == course_id:
                return course
        return None
    
    def match_courses_by_user_input(self, user_input):
        """根据用户输入匹配课程"""
        logger.info(f"根据用户输入匹配课程: {user_input}")
        matched_courses = []
        
        # 提取关键词
        keywords = []
        if '电商' in user_input or '电商运营' in user_input:
            keywords.append('电商')
        if '跨境' in user_input:
            keywords.append('跨境')
        if '入门' in user_input or '基础' in user_input:
            keywords.append('入门')
        if '进阶' in user_input or '高级' in user_input:
            keywords.append('进阶')
        if '转行' in user_input:
            keywords.append('转行')
        if '培训' in user_input:
            keywords.append('培训')
        
        # 匹配逻辑
        for course in self.courses:
            match_score = 0
            
            # 标题匹配
            if any(keyword in course['title'] for keyword in keywords):
                match_score += 3
            
            # 内容匹配
            if any(keyword in course['content'] for keyword in keywords):
                match_score += 2
            
            # 类别匹配
            if any(keyword in course['category'] for keyword in keywords):
                match_score += 1
            
            # 学历匹配
            if '初中' in user_input:
                if '初中及以上' in course['key_info']:
                    match_score += 2
            
            # 基础匹配
            if '零基础' in user_input or '零电商基础' in user_input:
                if '零基础' in course['key_info']:
                    match_score += 3
            
            # 转行需求匹配
            if '转行' in user_input:
                if '转行' in course['content'] or '就业' in course['content']:
                    match_score += 2
            
            if match_score > 0:
                matched_courses.append((course, match_score))
        
        # 按匹配分数排序
        matched_courses.sort(key=lambda x: x[1], reverse=True)
        
        # 只返回课程对象
        result = [course for course, score in matched_courses]
        logger.info(f"匹配到 {len(result)} 门课程: {[course['course_id'] for course in result]}")
        return result
    
    def match_courses_by_user_profile(self, user_profile):
        """根据用户画像匹配课程"""
        logger.info(f"根据用户画像匹配课程: {user_profile.get('user_id')}")
        matched_courses = []
        
        # 获取用户特征
        education = user_profile.get('basic_info', {}).get('education', '')
        skills = user_profile.get('basic_info', {}).get('skills', [])
        status = user_profile.get('basic_info', {}).get('status', '')
        core_needs = user_profile.get('core_needs', [])
        job_interest = user_profile.get('job_interest', [])
        
        # 匹配逻辑
        for course in self.courses:
            match_score = 0
            
            # 学历匹配
            if '初中及以上' in course['key_info'] and ('初中' in education or '高中' in education):
                match_score += 2
            
            # 身份匹配（失业人员）
            if status == '失业' and '失业人员可申请补贴' in course['key_info']:
                match_score += 3
            
            # 需求匹配
            if any('补贴' in need for need in core_needs):
                if 'POLICY_A02' in course['policy_relations']:
                    match_score += 2
            
            # 职业兴趣匹配
            if any('电商' in interest or '运营' in interest for interest in job_interest):
                if '电商' in course['title'] or '电商' in course['content']:
                    match_score += 2
            
            # 技能匹配
            if skills:
                # 这里可以根据实际情况扩展技能匹配逻辑
                pass
            
            if match_score > 0:
                matched_courses.append((course, match_score))
        
        # 按匹配分数排序
        matched_courses.sort(key=lambda x: x[1], reverse=True)
        
        # 只返回课程对象
        result = [course for course, score in matched_courses]
        logger.info(f"根据画像匹配到 {len(result)} 门课程: {[course['course_id'] for course in result]}")
        return result
    
    def recommend_courses(self, user_input=None, user_profile=None):
        """综合推荐课程"""
        logger.info("开始综合推荐课程")
        
        # 初始化推荐结果
        recommended = []
        
        # 根据用户输入匹配
        if user_input:
            input_matched = self.match_courses_by_user_input(user_input)
            recommended.extend(input_matched)
        
        # 根据用户画像匹配
        if user_profile:
            profile_matched = self.match_courses_by_user_profile(user_profile)
            recommended.extend(profile_matched)
        
        # 去重
        seen_course_ids = set()
        unique_courses = []
        for course in recommended:
            if course['course_id'] not in seen_course_ids:
                seen_course_ids.add(course['course_id'])
                unique_courses.append(course)
        
        # 场景四特殊处理：确保COURSE_A01优先于COURSE_A02
        # 1. 提取COURSE_A01和COURSE_A02
        course_a01 = None
        course_a02 = None
        other_courses = []
        
        for course in unique_courses:
            if course['course_id'] == 'COURSE_A01':
                course_a01 = course
            elif course['course_id'] == 'COURSE_A02':
                course_a02 = course
            else:
                other_courses.append(course)
        
        # 2. 构建优先级排序
        prioritized_courses = []
        if course_a01:
            prioritized_courses.append(course_a01)
        if course_a02:
            prioritized_courses.append(course_a02)
        prioritized_courses.extend(other_courses)
        
        # 3. 通用优先级排序（针对其他课程）
        # 优先推荐适合零基础的课程
        # 优先推荐失业人员可申请补贴的课程
        # 优先推荐入门级课程
        prioritized_courses.sort(key=lambda x: (
            x['course_id'] == 'COURSE_A01',  # COURSE_A01最优先
            x['course_id'] == 'COURSE_A02',  # COURSE_A02次之
            '零基础' in x['key_info'],
            '失业人员可申请补贴' in x['key_info'],
            '入门级' in x['difficulty']
        ), reverse=True)
        
        logger.info(f"最终推荐 {len(prioritized_courses)} 门课程: {[course['course_id'] for course in prioritized_courses]}")
        return prioritized_courses
    
    def get_course_with_policy(self, course_id):
        """获取课程及其关联的政策"""
        course = self.get_course_by_id(course_id)
        if not course:
            return None
        
        # 这里可以扩展获取关联政策的逻辑
        return course
    
    def match_courses_for_scenario4(self, user_input, user_profile=None):
        """场景四专用课程匹配方法"""
        logger.info("场景四专用课程匹配")
        
        # 1. 综合推荐课程
        recommended_courses = self.recommend_courses(user_input, user_profile)
        
        # 2. 确保只返回COURSE_A01和COURSE_A02
        scenario4_courses = []
        for course in recommended_courses:
            if course['course_id'] in ['COURSE_A01', 'COURSE_A02']:
                scenario4_courses.append(course)
        
        # 3. 确保COURSE_A01优先
        final_courses = []
        course_a01 = next((c for c in scenario4_courses if c['course_id'] == 'COURSE_A01'), None)
        course_a02 = next((c for c in scenario4_courses if c['course_id'] == 'COURSE_A02'), None)
        
        if course_a01:
            final_courses.append(course_a01)
        if course_a02:
            final_courses.append(course_a02)
        
        logger.info(f"场景四推荐课程: {[course['course_id'] for course in final_courses]}")
        return final_courses
    
    def get_course_package(self, courses, policy):
        """生成课程+补贴打包方案"""
        logger.info("生成课程+补贴打包方案")
        
        package = {
            "courses": [],
            "policy": policy,
            "estimated_benefit": 0
        }
        
        for course in courses:
            course_info = {
                "course_id": course['course_id'],
                "title": course['title'],
                "description": course['content'],
                "duration": course['duration'],
                "difficulty": course['difficulty'],
                "fee": course['fee'],
                "certificate": next((b['value'] for b in course['benefits'] if b['type'] == '证书'), ''),
                "employment_direction": next((b['value'] for b in course['benefits'] if b['type'] == '就业方向'), '')
            }
            package["courses"].append(course_info)
        
        # 计算预估收益（基于POLICY_A02）
        if policy and policy['policy_id'] == 'POLICY_A02':
            # 假设每门课程都能获得补贴
            for course in courses:
                if '初级' in course['difficulty']:
                    package["estimated_benefit"] += 1000
                elif '中级' in course['difficulty']:
                    package["estimated_benefit"] += 1500
                elif '高级' in course['difficulty']:
                    package["estimated_benefit"] += 2000
        
        logger.info(f"生成的打包方案包含 {len(package['courses'])} 门课程，预估收益: {package['estimated_benefit']}元")
        return package
    
    def generate_growth_path(self, courses):
        """勾勒成长路径"""
        logger.info("勾勒成长路径")
        
        if not courses:
            return []
        
        growth_path = []
        
        # 第一阶段：基础培训
        if any(c['course_id'] == 'COURSE_A01' for c in courses):
            growth_path.append({
                "stage": "第一阶段",
                "title": "基础培训",
                "content": "参加《电商运营入门实战班》（COURSE_A01），学习电商运营基础知识，掌握店铺搭建、产品上架、流量运营等核心技能，获取初级电商运营职业资格证书。",
                "duration": "3个月",
                "outcome": "具备电商运营基础能力，可应聘电商运营专员、店铺运营等岗位"
            })
        
        # 第二阶段：进阶学习
        if any(c['course_id'] == 'COURSE_A02' for c in courses):
            growth_path.append({
                "stage": "第二阶段",
                "title": "进阶学习",
                "content": "参加《跨境电商基础课程》（COURSE_A02），学习跨境电商平台规则、国际物流、海外营销等知识，提升电商运营层次。",
                "duration": "2个月",
                "outcome": "具备跨境电商运营能力，可应聘跨境电商运营、国际市场拓展等岗位"
            })
        
        # 第三阶段：就业/创业
        growth_path.append({
            "stage": "第三阶段",
            "title": "就业/创业",
            "content": "根据所学技能，选择适合的就业方向或自主创业。就业方向包括电商运营专员、跨境电商运营等；创业方向包括开设网店、电商服务等。",
            "duration": "长期",
            "outcome": "实现职业转型，获得稳定收入或创业成功"
        })
        
        logger.info(f"生成的成长路径包含 {len(growth_path)} 个阶段")
        return growth_path

# 测试代码
if __name__ == "__main__":
    matcher = CourseMatcher()
    
    # 测试场景四用户输入
    print("=== 测试场景四：培训课程智能匹配 ===")
    user_input = "我今年38岁，之前在工厂做机械操作工，现在失业了，只有初中毕业证，想转行做电商运营，不知道该报什么培训课程？另外，失业人员参加培训有补贴吗？"
    
    # 测试用户画像
    user_profile = {
        "user_id": "USER_TEST",
        "basic_info": {
            "age": 38,
            "gender": "男",
            "education": "初中",
            "status": "失业"
        },
        "core_needs": ["就业推荐", "培训补贴"],
        "job_interest": ["电商运营"]
    }
    
    # 测试场景四专用匹配
    scenario4_courses = matcher.match_courses_for_scenario4(user_input, user_profile)
    print("场景四推荐课程:")
    for course in scenario4_courses:
        print(f"- {course['course_id']}: {course['title']}")
    
    # 测试打包方案
    print("\n=== 测试课程+补贴打包方案 ===")
    # 模拟POLICY_A02
    policy_a02 = {
        "policy_id": "POLICY_A02",
        "title": "职业技能提升补贴政策",
        "content": "企业在职职工或失业人员取得初级/中级/高级职业资格证书（或职业技能等级证书），可在证书核发之日起12个月内申请补贴，标准分别为1000元/1500元/2000元。"
    }
    package = matcher.get_course_package(scenario4_courses, policy_a02)
    print(f"打包方案包含 {len(package['courses'])} 门课程")
    print(f"预估补贴收益: {package['estimated_benefit']}元")
    
    # 测试成长路径
    print("\n=== 测试成长路径 ===")
    growth_path = matcher.generate_growth_path(scenario4_courses)
    for stage in growth_path:
        print(f"{stage['stage']}: {stage['title']}")
        print(f"  内容: {stage['content']}")
        print(f"  时长: {stage['duration']}")
        print(f"  成果: {stage['outcome']}")
        print()