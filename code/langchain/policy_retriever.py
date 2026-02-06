import json
import os
import logging
from .job_matcher import JobMatcher
from .course_matcher import CourseMatcher
from .user_profile import UserProfileManager
from .chatbot import ChatBot

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - PolicyRetriever - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PolicyRetriever:
    def __init__(self, job_matcher=None, user_profile_manager=None, course_matcher=None):
        """初始化政策检索器"""
        # 缓存数据
        self._policies_cache = None
        self._policies_loaded = False
        self.policies = self.load_policies()
        self.job_matcher = job_matcher if job_matcher else JobMatcher()
        self.course_matcher = course_matcher if course_matcher else CourseMatcher()
        self.user_profile_manager = user_profile_manager if user_profile_manager else UserProfileManager(self.job_matcher)
        self.chatbot = ChatBot()
    
    def load_policies(self):
        """加载政策数据（带缓存）"""
        if self._policies_loaded and self._policies_cache:
            return self._policies_cache
        
        policy_file = os.path.join(os.path.dirname(__file__), 'data', 'policies.json')
        try:
            with open(policy_file, 'r', encoding='utf-8') as f:
                policies = json.load(f)
                # 缓存数据
                self._policies_cache = policies
                self._policies_loaded = True
                return policies
        except Exception as e:
            print(f"加载政策数据失败: {e}")
            return []
    
    def retrieve_policies(self, intent, entities, original_input=None):
        """检索相关政策"""
        relevant_policies = []
        logger.info(f"开始检索政策，意图: {intent}, 实体: {entities}")
        
        # 提取实体值和用户可能的需求关键词
        entity_values = [entity["value"] for entity in entities]
        logger.info(f"实体值列表: {entity_values}")
        
        # 检查用户具体条件 - 同时考虑实体值和原始用户输入
        entity_input_str = "".join(entity_values)
        # 使用原始用户输入作为备用，确保所有信息都被考虑
        user_input_str = original_input if original_input else entity_input_str
        logger.info(f"使用的用户输入字符串: {user_input_str}")
        
        has_certificate = "电工证" in user_input_str or "证书" in user_input_str
        is_unemployed = "失业" in user_input_str
        has_return_home = "返乡" in user_input_str or "农民工" in user_input_str
        has_entrepreneurship = "创业" in user_input_str or "小微企业" in user_input_str
        has_incubator = "场地补贴" in user_input_str or "孵化基地" in user_input_str or "租金" in user_input_str
        has_veteran = "退役军人" in user_input_str
        has_individual_business = "个体经营" in user_input_str or "开店" in user_input_str or "汽车维修店" in user_input_str or "维修店" in user_input_str or "经营" in user_input_str
        
        logger.info(f"用户条件检测: 证书={has_certificate}, 失业={is_unemployed}, 返乡={has_return_home}, 创业={has_entrepreneurship}, 孵化基地={has_incubator}, 退役军人={has_veteran}, 个体经营={has_individual_business}")
        
        # 逐个检查政策是否符合用户条件
        for policy in self.policies:
            policy_id = policy["policy_id"]
            title = policy["title"]
            conditions = policy.get("conditions", [])
            
            logger.info(f"检查政策: {policy_id} - {title}")
            
            # 根据政策ID和用户条件判断是否符合
            is_eligible = False
            
            if policy_id == "POLICY_A02":  # 职业技能提升补贴政策
                # 条件：持有职业资格证书或失业人员
                if has_certificate or is_unemployed:
                    is_eligible = True
                    logger.info(f"用户符合 {policy_id} 条件: 持有证书或失业")
            
            elif policy_id == "POLICY_A03":  # 返乡创业扶持补贴政策
                # 条件：返乡人员，创办小微企业，经营满1年，带动3人以上就业
                if has_return_home and has_entrepreneurship:
                    # 这里简化处理，实际需要更多条件验证
                    is_eligible = True
                    logger.info(f"用户符合 {policy_id} 条件: 返乡创业")
            
            elif policy_id == "POLICY_A04":  # 创业场地租金补贴政策
                # 条件：入驻创业孵化基地
                if has_incubator:
                    is_eligible = True
                    logger.info(f"用户符合 {policy_id} 条件: 入驻孵化基地")
            
            elif policy_id == "POLICY_A01":  # 创业担保贷款贴息政策
                # 条件：创业者身份（高校毕业生/返乡农民工/退役军人）
                if has_return_home or has_veteran:
                    is_eligible = True
                    logger.info(f"用户符合 {policy_id} 条件: 返乡人员或退役军人")
            
            elif policy_id == "POLICY_A05":  # 技能培训生活费补贴政策
                # 条件：脱贫人口、低保家庭成员、残疾人等
                if any(keyword in user_input_str for keyword in ["脱贫", "低保", "残疾"]):
                    is_eligible = True
                    logger.info(f"用户符合 {policy_id} 条件: 特殊群体")
            
            elif policy_id == "POLICY_A06":  # 退役军人创业税收优惠
                # 条件：退役军人且从事个体经营
                if has_veteran and has_individual_business:
                    is_eligible = True
                    logger.info(f"用户符合 {policy_id} 条件: 退役军人且从事个体经营")
            
            # 如果符合条件，添加到相关政策列表
            if is_eligible:
                relevant_policies.append(policy)
                logger.info(f"添加符合条件的政策: {policy_id} - {title}")
        
        # 限制返回的政策数量
        relevant_policies = relevant_policies[:3]
        
        logger.info(f"政策检索完成，找到 {len(relevant_policies)} 条符合条件的政策: {[p['policy_id'] for p in relevant_policies]}")
        return relevant_policies if relevant_policies else []
    
    def process_query(self, user_input, intent_info):
        """处理用户查询"""
        logger.info(f"处理用户查询: {user_input[:50]}...")
        
        # 检查是否需要各项服务
        needs_job_recommendation = intent_info.get("needs_job_recommendation", False)
        needs_course_recommendation = intent_info.get("needs_course_recommendation", False)
        needs_policy_recommendation = intent_info.get("needs_policy_recommendation", False)
        
        # 1. 生成岗位推荐（仅当用户需要时）
        recommended_jobs = []
        if needs_job_recommendation:
            logger.info("用户需要岗位推荐，开始处理")
            # 直接基于用户输入和实体匹配岗位，不依赖政策
            # 提取实体信息用于岗位匹配
            entities = intent_info.get("entities", [])
            
            # 基于用户输入和实体匹配岗位
            matched_jobs = self.job_matcher.match_jobs_by_entities(entities)
            recommended_jobs.extend(matched_jobs)
            
            # 去重
            seen_job_ids = set()
            unique_jobs = []
            for job in recommended_jobs:
                job_id = job.get("job_id")
                if job_id not in seen_job_ids:
                    seen_job_ids.add(job_id)
                    unique_jobs.append(job)
            recommended_jobs = unique_jobs[:3]  # 最多返回3个岗位
            logger.info(f"生成了 {len(recommended_jobs)} 个岗位推荐")
        
        # 2. 检索相关政策（仅当用户需要时）
        relevant_policies = []
        if needs_policy_recommendation:
            logger.info("用户需要政策推荐，开始处理")
            relevant_policies = self.retrieve_policies(intent_info["intent"], intent_info["entities"], user_input)
        
        # 3. 生成课程推荐（仅当用户需要时）
        recommended_courses = []
        if needs_course_recommendation:
            logger.info("用户需要课程推荐，开始处理")
            # 基于政策关联课程
            if relevant_policies:
                for policy in relevant_policies:
                    policy_id = policy.get("policy_id")
                    # 简单示例：基于政策ID匹配课程
                    if policy_id == "POLICY_A02":  # 技能提升补贴政策
                        # 匹配相关课程
                        matched_courses = self.course_matcher.match_courses_by_policy(policy_id)
                        recommended_courses.extend(matched_courses)
            
            # 去重
            seen_course_ids = set()
            unique_courses = []
            for course in recommended_courses:
                course_id = course.get("course_id")
                if course_id not in seen_course_ids:
                    seen_course_ids.add(course_id)
                    unique_courses.append(course)
            
            # 只推荐符合条件的课程（COURSE_A01、COURSE_A02）
            filtered_courses = []
            for course in unique_courses:
                course_id = course.get("course_id")
                if course_id in ['COURSE_A01', 'COURSE_A02']:
                    filtered_courses.append(course)
            
            # 确保COURSE_A01优先
            final_courses = []
            course_a01 = next((c for c in filtered_courses if c['course_id'] == 'COURSE_A01'), None)
            course_a02 = next((c for c in filtered_courses if c['course_id'] == 'COURSE_A02'), None)
            if course_a01:
                final_courses.append(course_a01)
            if course_a02:
                final_courses.append(course_a02)
            
            recommended_courses = final_courses
            logger.info(f"生成了 {len(recommended_courses)} 个课程推荐: {[course['course_id'] for course in recommended_courses]}")
        
        return {
            "relevant_policies": relevant_policies,
            "recommended_jobs": recommended_jobs,
            "recommended_courses": recommended_courses
        }
    
    def analyze_input(self, user_input, conversation_history=None):
        """分析用户输入，判断是否需要收集更多信息"""
        logger.info(f"分析用户输入: {user_input[:50]}...")
        
        # 1. 快速检查是否为政策咨询相关输入
        policy_keywords = ["政策", "补贴", "贷款", "申请", "返乡", "创业", "小微企业"]
        if any(keyword in user_input for keyword in policy_keywords):
            # 政策咨询不需要收集详细个人信息
            logger.info("识别到政策咨询输入，跳过详细信息收集")
            return {
                "matched_user": None,
                "required_info": {},
                "missing_info": [],
                "needs_more_info": False
            }
        
        # 2. 匹配用户画像
        matched_user = self.user_profile_manager.match_user_profile(user_input)
        
        # 3. 分析需要的信息
        # 基于数据文件分析，优化信息收集要素
        required_info = {
            "user_profile": {
                "required": ["education", "skills", "work_experience", "identity", "status"],
                "available": []
            },
            "user_needs": {
                "required": ["specific_needs", "timeframe", "location", "salary_range", "job_interest"],
                "available": []
            }
        }
        
        # 3. 检查现有信息
        if matched_user and isinstance(matched_user, dict):
            user_data = matched_user.get("data", {})
            basic_info = matched_user.get("basic_info", {})
            
            # 从用户画像中提取身份信息
            identity = basic_info.get("identity", "")
            status = basic_info.get("status", "")
            logger.info(f"匹配到用户身份: {identity}, 状态: {status}")
            
            # 将用户画像中的信息添加到现有可用信息列表中
            # 添加基本信息
            for key, value in basic_info.items():
                if key not in required_info["user_profile"]["available"]:
                    required_info["user_profile"]["available"].append(key)
                    logger.info(f"从用户画像中提取到{key}信息: {value}")
            
            # 添加其他用户数据
            for key in user_data.keys():
                if key not in required_info["user_profile"]["available"]:
                    required_info["user_profile"]["available"].append(key)
            
            # 从core_needs中提取specific_needs
            core_needs = matched_user.get("core_needs", [])
            if core_needs:
                if "specific_needs" not in required_info["user_needs"]["available"]:
                    required_info["user_needs"]["available"].append("specific_needs")
                    logger.info(f"从用户画像中提取到需求信息: {core_needs}")
            
            # 从job_interest中提取job_interest
            job_interest = matched_user.get("job_interest", [])
            if job_interest:
                if "job_interest" not in required_info["user_needs"]["available"]:
                    required_info["user_needs"]["available"].append("job_interest")
                    logger.info(f"从用户画像中提取到岗位兴趣: {job_interest}")
            
            # 基于用户身份预测可用信息
            if identity == "返乡农民工":
                # 返乡农民工通常需要创业扶持政策
                if "specific_needs" not in required_info["user_needs"]["available"]:
                    required_info["user_needs"]["available"].append("specific_needs")
                    logger.info("基于返乡农民工身份预测需求信息")
                if "location" not in required_info["user_needs"]["available"]:
                    required_info["user_needs"]["available"].append("location")
                    logger.info("基于返乡农民工身份预测地点信息")
            elif identity == "高校毕业生":
                # 高校毕业生通常有学历信息
                if "education" not in required_info["user_profile"]["available"]:
                    required_info["user_profile"]["available"].append("education")
                    logger.info("基于高校毕业生身份预测学历信息")
                if "specific_needs" not in required_info["user_needs"]["available"]:
                    required_info["user_needs"]["available"].append("specific_needs")
                    logger.info("基于高校毕业生身份预测需求信息")
            elif identity == "退役军人":
                # 退役军人通常有特定的政策需求
                if "specific_needs" not in required_info["user_needs"]["available"]:
                    required_info["user_needs"]["available"].append("specific_needs")
                    logger.info("基于退役军人身份预测需求信息")
                if "location" not in required_info["user_needs"]["available"]:
                    required_info["user_needs"]["available"].append("location")
                    logger.info("基于退役军人身份预测地点信息")
            elif identity == "失业人员":
                # 失业人员通常需要技能培训和就业服务
                if "specific_needs" not in required_info["user_needs"]["available"]:
                    required_info["user_needs"]["available"].append("specific_needs")
                    logger.info("基于失业人员身份预测需求信息")
                if "skills" not in required_info["user_profile"]["available"]:
                    required_info["user_profile"]["available"].append("skills")
                    logger.info("基于失业人员身份预测技能信息")
            elif identity == "脱贫人口":
                # 脱贫人口通常需要技能培训和生活费补贴
                if "specific_needs" not in required_info["user_needs"]["available"]:
                    required_info["user_needs"]["available"].append("specific_needs")
                    logger.info("基于脱贫人口身份预测需求信息")
                if "education" not in required_info["user_profile"]["available"]:
                    required_info["user_profile"]["available"].append("education")
                    logger.info("基于脱贫人口身份预测学历信息")
        
        # 4. 从当前用户输入中提取信息
        # 检查用户输入中是否包含学历相关词汇
        education_keywords = ["本科", "硕士", "博士", "高中", "中专", "大专", "研究生", "初中", "小学", "学历"]
        for keyword in education_keywords:
            if keyword in user_input and "education" not in required_info["user_profile"]["available"]:
                required_info["user_profile"]["available"].append("education")
                logger.info(f"从用户输入中提取到学历信息: {keyword}")
                break
        
        # 检查用户输入中是否包含技能相关词汇
        skills_keywords = ["技能", "证书", "资格证", "执业证", "许可证", "职业资格", "技能等级"]
        for keyword in skills_keywords:
            if keyword in user_input and "skills" not in required_info["user_profile"]["available"]:
                required_info["user_profile"]["available"].append("skills")
                logger.info(f"从用户输入中提取到技能信息: {keyword}")
                break
        
        # 检查用户输入中是否包含经验相关词汇
        experience_keywords = ["经验", "工作", "实习", "实践", "工龄", "年限"]
        for keyword in experience_keywords:
            if keyword in user_input and "work_experience" not in required_info["user_profile"]["available"]:
                required_info["user_profile"]["available"].append("work_experience")
                logger.info(f"从用户输入中提取到工作经验信息: {keyword}")
                break
        
        # 检查用户输入中是否包含身份相关词汇
        identity_keywords = ["返乡农民工", "高校毕业生", "退役军人", "失业人员", "脱贫人口", "低保", "残疾人"]
        for keyword in identity_keywords:
            if keyword in user_input and "identity" not in required_info["user_profile"]["available"]:
                required_info["user_profile"]["available"].append("identity")
                logger.info(f"从用户输入中提取到身份信息: {keyword}")
                break
        
        # 检查用户输入中是否包含状态相关词汇
        status_keywords = ["失业", "在职", "创业", "培训", "求职", "筹备", "经营"]
        for keyword in status_keywords:
            if keyword in user_input and "status" not in required_info["user_profile"]["available"]:
                required_info["user_profile"]["available"].append("status")
                logger.info(f"从用户输入中提取到状态信息: {keyword}")
                break
        
        # 检查用户输入中是否包含需求相关词汇
        needs_keywords = ["需要", "需求", "要求", "希望", "想", "询问", "咨询", "了解", "申请", "领取", "怎么", "如何", "能否", "能领", "创业", "贷款", "补贴", "政策", "优惠", "扶持"]
        for keyword in needs_keywords:
            if keyword in user_input and "specific_needs" not in required_info["user_needs"]["available"]:
                required_info["user_needs"]["available"].append("specific_needs")
                logger.info(f"从用户输入中提取到需求信息: {keyword}")
                break
        
        # 检查用户输入中是否包含时间相关词汇
        time_keywords = ["时间", "期限", "多久", "什么时候", "时长", "周期"]
        for keyword in time_keywords:
            if keyword in user_input and "timeframe" not in required_info["user_needs"]["available"]:
                required_info["user_needs"]["available"].append("timeframe")
                logger.info(f"从用户输入中提取到时间信息: {keyword}")
                break
        
        # 检查用户输入中是否包含地点相关词汇
        location_keywords = ["地点", "地区", "哪里", "位置", "北京", "上海", "广州", "深圳", "家乡", "家", "当地", "城市", "地区"]
        for keyword in location_keywords:
            if keyword in user_input and "location" not in required_info["user_needs"]["available"]:
                required_info["user_needs"]["available"].append("location")
                logger.info(f"从用户输入中提取到地点信息: {keyword}")
                break
        
        # 检查用户输入中是否包含薪资相关词汇
        salary_keywords = ["薪资", "工资", "收入", "待遇", "月薪", "年薪", "薪资范围"]
        for keyword in salary_keywords:
            if keyword in user_input and "salary_range" not in required_info["user_needs"]["available"]:
                required_info["user_needs"]["available"].append("salary_range")
                logger.info(f"从用户输入中提取到薪资信息: {keyword}")
                break
        
        # 检查用户输入中是否包含岗位兴趣相关词汇
        job_interest_keywords = ["想做", "希望做", "打算做", "感兴趣", "职业", "岗位", "工作"]
        for keyword in job_interest_keywords:
            if keyword in user_input and "job_interest" not in required_info["user_needs"]["available"]:
                required_info["user_needs"]["available"].append("job_interest")
                logger.info(f"从用户输入中提取到岗位兴趣信息: {keyword}")
                break
        
        # 5. 处理用户回答"没有"的情况
        negative_keywords = ["没有", "无", "none", "no"]
        is_negative_answer = any(keyword in user_input.lower() for keyword in negative_keywords)
        
        # 6. 从对话历史中提取信息，特别处理用户回答
        if conversation_history and isinstance(conversation_history, list):
            logger.info(f"对话历史长度: {len(conversation_history)}")
            
            # 遍历对话历史，处理问答对
            i = 0
            while i < len(conversation_history):
                msg = conversation_history[i]
                if isinstance(msg, dict):
                    role = msg.get("role")
                    content = msg.get("content", "")
                    
                    # 查找AI提问和用户回答的配对
                    if role == "ai" and i + 1 < len(conversation_history):
                        next_msg = conversation_history[i + 1]
                        if isinstance(next_msg, dict) and next_msg.get("role") == "user":
                            user_answer = next_msg.get("content", "")
                            
                            # 尝试解析AI消息
                            ai_message_content = content
                            try:
                                ai_message_data = json.loads(content)
                                if isinstance(ai_message_data, dict):
                                    if "question" in ai_message_data:
                                        ai_message_content = ai_message_data["question"]
                                    elif "content" in ai_message_data:
                                        ai_message_content = ai_message_data["content"]
                                    elif "question" in ai_message_data.get("data", {}):
                                        ai_message_content = ai_message_data["data"]["question"]
                            except:
                                pass
                            
                            logger.info(f"AI消息: {ai_message_content}")
                            logger.info(f"用户回答: {user_answer}")
                            
                            # 处理问答对
                            if "学历" in ai_message_content:
                                if "education" not in required_info["user_profile"]["available"]:
                                    required_info["user_profile"]["available"].append("education")
                                    logger.info("从对话历史中提取到学历信息")
                            elif "技能" in ai_message_content:
                                if "skills" not in required_info["user_profile"]["available"]:
                                    required_info["user_profile"]["available"].append("skills")
                                    logger.info("从对话历史中提取到技能信息")
                            elif "经验" in ai_message_content:
                                if "work_experience" not in required_info["user_profile"]["available"]:
                                    required_info["user_profile"]["available"].append("work_experience")
                                    logger.info("从对话历史中提取到工作经验信息")
                            elif "需要" in ai_message_content or "需求" in ai_message_content:
                                if "specific_needs" not in required_info["user_needs"]["available"]:
                                    required_info["user_needs"]["available"].append("specific_needs")
                                    logger.info("从对话历史中提取到需求信息")
                            elif "时间" in ai_message_content or "期限" in ai_message_content:
                                if "timeframe" not in required_info["user_needs"]["available"]:
                                    required_info["user_needs"]["available"].append("timeframe")
                                    logger.info("从对话历史中提取到时间信息")
                            elif "地点" in ai_message_content or "地区" in ai_message_content:
                                if "location" not in required_info["user_needs"]["available"]:
                                    required_info["user_needs"]["available"].append("location")
                                    logger.info("从对话历史中提取到地点信息")
                i += 1
        
        # 7. 从上下文中理解用户回答，特别是最后一个问答对
        if conversation_history and isinstance(conversation_history, list) and len(conversation_history) >= 2:
            # 查找最后一个AI消息和最后一个用户消息
            last_ai_message = None
            last_user_message = None
            
            for msg in reversed(conversation_history):
                if isinstance(msg, dict):
                    if msg.get("role") == "ai" and not last_ai_message:
                        last_ai_message = msg.get("content", "")
                    elif msg.get("role") == "user" and not last_user_message:
                        last_user_message = msg.get("content", "")
                    
                    if last_ai_message and last_user_message:
                        break
            
            if last_ai_message and last_user_message:
                # 尝试解析AI消息
                ai_message_content = last_ai_message
                try:
                    ai_message_data = json.loads(last_ai_message)
                    if isinstance(ai_message_data, dict):
                        if "question" in ai_message_data:
                            ai_message_content = ai_message_data["question"]
                        elif "content" in ai_message_data:
                            ai_message_content = ai_message_data["content"]
                        elif "question" in ai_message_data.get("data", {}):
                            ai_message_content = ai_message_data["data"]["question"]
                except:
                    pass
                
                logger.info(f"最后一个AI消息: {ai_message_content}")
                logger.info(f"最后一个用户回答: {last_user_message}")
                
                # 只要用户回答了问题，就认为该信息已提供，无论回答是什么
                if "学历" in ai_message_content:
                    if "education" not in required_info["user_profile"]["available"]:
                        required_info["user_profile"]["available"].append("education")
                        logger.info("从最后一个问答对中提取到学历信息")
                elif "技能" in ai_message_content:
                    if "skills" not in required_info["user_profile"]["available"]:
                        required_info["user_profile"]["available"].append("skills")
                        logger.info("从最后一个问答对中提取到技能信息")
                elif "经验" in ai_message_content:
                    if "work_experience" not in required_info["user_profile"]["available"]:
                        required_info["user_profile"]["available"].append("work_experience")
                        logger.info("从最后一个问答对中提取到工作经验信息")
                elif "需要" in ai_message_content or "需求" in ai_message_content:
                    if "specific_needs" not in required_info["user_needs"]["available"]:
                        required_info["user_needs"]["available"].append("specific_needs")
                        logger.info("从最后一个问答对中提取到需求信息")
                elif "时间" in ai_message_content or "期限" in ai_message_content:
                    if "timeframe" not in required_info["user_needs"]["available"]:
                        required_info["user_needs"]["available"].append("timeframe")
                        logger.info("从最后一个问答对中提取到时间信息")
                elif "地点" in ai_message_content or "地区" in ai_message_content:
                    if "location" not in required_info["user_needs"]["available"]:
                        required_info["user_needs"]["available"].append("location")
                        logger.info("从最后一个问答对中提取到地点信息")
        
        # 8. 智能过滤不必要的信息需求
        # 基于用户输入和对话历史，过滤掉明显不需要的信息
        if is_negative_answer:
            # 用户回答"没有"，标记所有当前正在询问的信息为已提供
            logger.info("用户回答'没有'，标记相关信息为已提供")
            # 检查对话历史，确定当前正在询问的信息类型
            if conversation_history and isinstance(conversation_history, list) and len(conversation_history) >= 2:
                last_ai_message = None
                for msg in reversed(conversation_history):
                    if isinstance(msg, dict) and msg.get("role") == "ai":
                        last_ai_message = msg.get("content", "")
                        break
                
                if last_ai_message:
                    # 尝试解析最后一个AI消息
                    ai_message_content = last_ai_message
                    try:
                        ai_message_data = json.loads(last_ai_message)
                        if isinstance(ai_message_data, dict):
                            if "question" in ai_message_data:
                                ai_message_content = ai_message_data["question"]
                            elif "content" in ai_message_data:
                                ai_message_content = ai_message_data["content"]
                    except:
                        pass
                    
                    # 根据AI问题类型，标记相应信息为已提供
                    if "学历" in ai_message_content:
                        if "education" not in required_info["user_profile"]["available"]:
                            required_info["user_profile"]["available"].append("education")
                            logger.info("用户回答'没有'，标记学历信息为已提供")
                    elif "技能" in ai_message_content:
                        if "skills" not in required_info["user_profile"]["available"]:
                            required_info["user_profile"]["available"].append("skills")
                            logger.info("用户回答'没有'，标记技能信息为已提供")
                    elif "经验" in ai_message_content:
                        if "work_experience" not in required_info["user_profile"]["available"]:
                            required_info["user_profile"]["available"].append("work_experience")
                            logger.info("用户回答'没有'，标记工作经验信息为已提供")
                    elif "需要" in ai_message_content or "需求" in ai_message_content:
                        if "specific_needs" not in required_info["user_needs"]["available"]:
                            required_info["user_needs"]["available"].append("specific_needs")
                            logger.info("用户回答'没有'，标记需求信息为已提供")
                    elif "时间" in ai_message_content or "期限" in ai_message_content:
                        if "timeframe" not in required_info["user_needs"]["available"]:
                            required_info["user_needs"]["available"].append("timeframe")
                            logger.info("用户回答'没有'，标记时间信息为已提供")
                    elif "地点" in ai_message_content or "地区" in ai_message_content:
                        if "location" not in required_info["user_needs"]["available"]:
                            required_info["user_needs"]["available"].append("location")
                            logger.info("用户回答'没有'，标记地点信息为已提供")
        
        # 9. 检查是否需要更多信息
        missing_info = []
        for category, info in required_info.items():
            for req in info["required"]:
                if req not in info["available"]:
                    missing_info.append(f"{category}.{req}")
        
        logger.info(f"可用信息: {required_info['user_profile']['available']}, {required_info['user_needs']['available']}")
        logger.info(f"缺失信息: {missing_info}")
        
        # 10. 智能判断是否需要追问
        # 基于用户身份和输入内容，判断是否真的需要追问
        should_ask = False
        important_missing_info = []
        
        # 定义重要信息类型
        important_info_types = [
            "user_needs.specific_needs",  # 具体需求是最重要的
            "user_needs.location"         # 地点信息对于政策匹配很重要
        ]
        
        # 筛选重要的缺失信息
        for info_type in missing_info:
            if info_type in important_info_types:
                important_missing_info.append(info_type)
                should_ask = True
        
        # 如果有重要信息缺失，或者缺失信息较少且用户身份明确，才进行追问
        if not should_ask and len(missing_info) > 0:
            # 检查用户身份
            if matched_user and isinstance(matched_user, dict):
                identity = matched_user.get("basic_info", {}).get("identity", "")
                if identity:
                    # 对于有明确身份的用户，即使有一些非重要信息缺失，也可以开始分析
                    logger.info(f"用户身份明确({identity})，即使有非重要信息缺失，也开始分析")
                    should_ask = False
                else:
                    # 对于身份不明确的用户，需要更多信息
                    should_ask = True
            else:
                # 对于没有匹配到用户画像的用户，如果缺失信息较多，需要追问
                should_ask = len(missing_info) > 2
        
        # 11. 生成追问
        if should_ask and (important_missing_info or missing_info):
            follow_up_questions = {
                "user_profile.education": "请问您的学历是什么？",
                "user_profile.skills": "请问您有哪些技能或证书？",
                "user_profile.work_experience": "请问您有多少年工作经验？",
                "user_needs.specific_needs": "请问您的具体需求是什么？",
                "user_needs.timeframe": "请问您的时间要求是什么？",
                "user_needs.location": "请问您的地点要求是什么？"
            }
            
            # 优化优先级排序，减少不必要的追问
            priority_order = []
            
            # 优先处理与用户身份相关的信息
            if matched_user and isinstance(matched_user, dict):
                identity = matched_user.get("basic_info", {}).get("identity", "")
                if identity == "返乡农民工":
                    # 返乡农民工优先需要地点和需求信息
                    priority_order = [
                        "user_needs.location",
                        "user_needs.specific_needs",
                        "user_profile.education",
                        "user_profile.skills",
                        "user_profile.work_experience",
                        "user_needs.timeframe"
                    ]
                elif identity == "高校毕业生":
                    # 高校毕业生优先需要需求和学历信息
                    priority_order = [
                        "user_needs.specific_needs",
                        "user_profile.education",
                        "user_needs.location",
                        "user_profile.skills",
                        "user_profile.work_experience",
                        "user_needs.timeframe"
                    ]
                elif identity == "退役军人":
                    # 退役军人优先需要需求和地点信息
                    priority_order = [
                        "user_needs.specific_needs",
                        "user_needs.location",
                        "user_profile.education",
                        "user_profile.skills",
                        "user_profile.work_experience",
                        "user_needs.timeframe"
                    ]
            
            # 如果没有基于身份的优先级排序，使用默认排序
            if not priority_order:
                priority_order = [
                    "user_needs.specific_needs",
                    "user_needs.location",
                    "user_profile.education",
                    "user_profile.skills",
                    "user_profile.work_experience",
                    "user_needs.timeframe"
                ]
            
            # 优先选择重要的缺失信息进行追问
            target_info_types = important_missing_info if important_missing_info else missing_info
            
            # 按照优先级顺序选择追问信息
            selected_info_type = None
            for info_type in priority_order:
                if info_type in target_info_types:
                    selected_info_type = info_type
                    break
            
            if selected_info_type:
                follow_up_question = follow_up_questions.get(selected_info_type, "请问您能提供更多信息吗？")
                logger.info(f"生成追问: {follow_up_question}")
                
                return {
                    "matched_user": matched_user,
                    "required_info": required_info,
                    "missing_info": missing_info,
                    "needs_more_info": True,
                    "follow_up_question": follow_up_question
                }
        
        # 12. 信息足够，返回分析结果
        logger.info("信息足够，开始分析")
        return {
            "matched_user": matched_user,
            "required_info": required_info,
            "missing_info": [],
            "needs_more_info": False
        }
    
    def process_analysis(self, analysis_result, user_input, session_id=None):
        """处理分析结果，生成最终回答"""
        logger.info(f"处理分析结果, session_id: {session_id}")
        
        # 1. 获取分析结果
        matched_user = analysis_result.get("matched_user")
        
        # 2. 获取所有数据
        all_policies = self.policies
        all_jobs = self.job_matcher.get_all_jobs()
        all_courses = self.course_matcher.get_all_courses()
        
        # 3. 构建分析Prompt
        prompt = self.build_analysis_prompt(user_input, matched_user, all_policies, all_jobs, all_courses)
        
        # 4. 调用LLM进行分析
        llm_response = self.chatbot.chat_with_memory(prompt)
        
        # 5. 处理LLM响应
        try:
            if isinstance(llm_response, dict):
                content = llm_response.get("content", "")
            else:
                content = llm_response if isinstance(llm_response, str) else str(llm_response)
            
            # 尝试解析JSON响应
            if isinstance(content, dict):
                return content
            else:
                return json.loads(content)
        except Exception as e:
            logger.error(f"解析分析结果失败: {str(e)}")
            return {
                "error": str(e)
            }
    
    def build_analysis_prompt(self, user_input, matched_user, all_policies, all_jobs, all_courses):
        """构建分析Prompt"""
        prompt = f"""
你是一个专业的政策咨询助手，负责根据用户输入和提供的政策、岗位、课程信息，生成结构化的分析结果。

用户输入: {user_input}

"""
        
        if matched_user:
            user_profile_str = f"匹配用户画像: {matched_user.get('user_id')} - {matched_user.get('description', '')}\n"
            prompt += user_profile_str
        
        prompt += "相关政策:\n"
        for policy in all_policies[:5]:  # 只使用前5个政策，避免输入过长
            prompt += f"- {policy.get('policy_id')}: {policy.get('title')} (分类: {policy.get('category')})\n"
        
        prompt += "\n相关岗位:\n"
        for job in all_jobs[:5]:  # 只使用前5个岗位，避免输入过长
            prompt += f"- {job.get('job_id')}: {job.get('title')}\n"
        
        prompt += "\n相关课程:\n"
        for course in all_courses[:5]:  # 只使用前5个课程，避免输入过长
            prompt += f"- {course.get('course_id')}: {course.get('title')} (分类: {course.get('category')})\n"
        
        prompt += "\n请根据以上信息，生成结构化的分析结果，包括：\n1. 识别用户的核心需求\n2. 匹配相关的政策、岗位和课程\n3. 提供具体的建议和下一步行动\n\n输出格式为JSON，包含以下字段：\n{\n  \"core_needs\": [\"核心需求1\", \"核心需求2\", ...],\n  \"matched_policies\": [{\"policy_id\": \"政策ID\", \"title\": \"政策标题\", \"relevance\": \"相关性\"}, ...],\n  \"matched_jobs\": [{\"job_id\": \"岗位ID\", \"title\": \"岗位标题\", \"relevance\": \"相关性\"}, ...],\n  \"matched_courses\": [{\"course_id\": \"课程ID\", \"title\": \"课程标题\", \"relevance\": \"相关性\"}, ...],\n  \"suggestions\": [\"建议1\", \"建议2\", ...]\n}\n"
        
        return prompt
