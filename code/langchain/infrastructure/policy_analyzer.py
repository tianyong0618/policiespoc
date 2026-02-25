import logging

logger = logging.getLogger(__name__)


class PolicyAnalyzer:
    """政策分析工具类，统一处理政策分析逻辑"""
    
    def __init__(self):
        """初始化政策分析器"""
        pass
    
    def analyze_policy_a03(self, user_input_str, has_employment):
        """分析 POLICY_A03 政策"""
        has_business = "小微企业" in user_input_str or "小加工厂" in user_input_str
        has_operation_time = "经营" in user_input_str or "正常经营" in user_input_str or "经营时间" in user_input_str
        
        if has_employment and has_business and has_operation_time:
            return {
                "step": "检索POLICY_A03",
                "content": "判断\"创办小微企业+正常经营1年+带动3人以上就业\"可申领2万一次性补贴，用户已提及所有条件，符合条件"
            }
        elif has_employment:
            missing_conditions = []
            if not has_business:
                missing_conditions.append("创办主体为小微企业")
            if not has_operation_time:
                missing_conditions.append("经营时间≥1年")
            if missing_conditions:
                return {
                    "step": "检索POLICY_A03",
                    "content": f"判断\"创办小微企业+正常经营1年+带动3人以上就业\"可申领2万一次性补贴，用户已提及带动就业，但未提及{', '.join(missing_conditions)}，需指出缺失条件"
                }
            else:
                return {
                    "step": "检索POLICY_A03",
                    "content": "判断\"创办小微企业+正常经营1年+带动3人以上就业\"可申领2万一次性补贴，用户已提及带动就业，符合条件"
                }
        else:
            return {
                "step": "检索POLICY_A03",
                "content": "判断\"创办小微企业+正常经营1年+带动3人以上就业\"可申领2万一次性补贴，用户未提\"带动就业\"，需指出缺失条件"
            }
    
    def analyze_policy_a01(self, user_input_str, intent_info):
        """分析 POLICY_A01 政策"""
        # 从实体中提取信息
        has_veteran_entity = False
        has_migrant_entity = False
        has_business_entity = False
        
        for entity in intent_info.get('entities', []):
            entity_type = entity.get('type', '')
            entity_value = entity.get('value', '')
            
            if entity_type == 'employment_status' and ('退役军人' in entity_value):
                has_veteran_entity = True
            elif entity_type == 'employment_status' and ('返乡农民工' in entity_value or '农民工' in entity_value or '返乡' in entity_value):
                has_migrant_entity = True
            elif entity_type == 'business_type' and ('小微企业' in entity_value or '小加工厂' in entity_value):
                has_business_entity = True
            elif entity_type == 'concern' and ('创业' in entity_value or '创业贷款' in entity_value):
                has_business_entity = True
        
        # 从用户输入中提取信息（作为备用）
        has_veteran_input = "退役军人" in user_input_str
        has_migrant_input = ("返乡农民工" in user_input_str or 
                           ("回来" in user_input_str and "农民工" in user_input_str) or
                           ("返乡" in user_input_str and "农民工" in user_input_str))
        has_business_input = "创业" in user_input_str or "企业" in user_input_str or "开店" in user_input_str or "汽车维修店" in user_input_str or "小微企业" in user_input_str or "小加工厂" in user_input_str
        
        # 综合判断
        has_veteran = has_veteran_entity or has_veteran_input
        has_migrant = has_migrant_entity or has_migrant_input
        has_identity = has_veteran or has_migrant
        has_business = has_business_entity or has_business_input
        
        if has_identity and has_business:
            identity_type = "退役军人" if has_veteran else "返乡农民工"
            return {
                "step": "检索POLICY_A01",
                "content": f"判断\"{identity_type}+创业\"可申请创业担保贷款贴息，用户已提及相关条件，符合条件"
            }
        else:
            missing_conditions = []
            if not has_identity:
                missing_conditions.append("返乡农民工或退役军人身份")
            if not has_business:
                missing_conditions.append("创业需求")
            if missing_conditions:
                return {
                    "step": "检索POLICY_A01",
                    "content": f"判断\"返乡农民工或退役军人+创业\"可申请创业担保贷款贴息，用户未提及{', '.join(missing_conditions)}，需指出缺失条件"
                }
            else:
                return {
                    "step": "检索POLICY_A01",
                    "content": "判断\"返乡农民工或退役军人+创业\"可申请创业担保贷款贴息，用户已提及所有条件，符合条件"
                }
    
    def analyze_policy_a02(self, user_input_str):
        """分析 POLICY_A02 政策"""
        has_certificate = "证书" in user_input_str or "职业资格" in user_input_str or "技能等级" in user_input_str or "证" in user_input_str
        has_employment = "在职" in user_input_str or "失业" in user_input_str or "就业" in user_input_str
        
        if has_certificate and has_employment:
            return {
                "step": "检索POLICY_A02",
                "content": "判断\"在职职工或失业人员+取得职业资格证书\"可申领技能提升补贴，用户已提及相关条件，符合条件"
            }
        else:
            missing_conditions = []
            if not has_certificate:
                missing_conditions.append("取得职业资格证书或职业技能等级证书")
            if not has_employment:
                missing_conditions.append("在职职工或失业人员身份")
            if missing_conditions:
                return {
                    "step": "检索POLICY_A02",
                    "content": f"判断\"在职职工或失业人员+取得职业资格证书\"可申领技能提升补贴，用户未提及{', '.join(missing_conditions)}，需指出缺失条件"
                }
            else:
                return {
                    "step": "检索POLICY_A02",
                    "content": "判断\"在职职工或失业人员+取得职业资格证书\"可申领技能提升补贴，用户已提及所有条件，符合条件"
                }
    
    def analyze_policy_a04(self, user_input_str):
        """分析 POLICY_A04 政策"""
        has_employment_base = "创业孵化基地" in user_input_str or "入驻" in user_input_str or "场地" in user_input_str
        has_business = "汽车维修店" in user_input_str or "小微企业" in user_input_str or "企业" in user_input_str or "创业" in user_input_str or "经营" in user_input_str or "网店运营" in user_input_str
        
        if has_employment_base and has_business:
            return {
                "step": "检索POLICY_A04",
                "content": "判断\"入驻创业孵化基地+创办企业\"可申领场地租金补贴，用户已提及入驻创业孵化基地和开汽车维修店，符合条件"
            }
        else:
            missing_conditions = []
            if not has_employment_base:
                missing_conditions.append("入驻创业孵化基地")
            if not has_business:
                missing_conditions.append("创办企业")
            if missing_conditions:
                return {
                    "step": "检索POLICY_A04",
                    "content": f"判断\"入驻创业孵化基地+创办企业\"可申领场地租金补贴，用户未提及{', '.join(missing_conditions)}，需指出缺失条件"
                }
            else:
                return {
                    "step": "检索POLICY_A04",
                    "content": "判断\"入驻创业孵化基地+创办企业\"可申领场地租金补贴，用户已提及所有条件，符合条件"
                }
    
    def analyze_policy_a06(self, user_input_str):
        """分析 POLICY_A06 政策"""
        has_veteran = "退役军人" in user_input_str
        has_individual_business = "个体经营" in user_input_str or "汽车维修店" in user_input_str or "开店" in user_input_str or "维修店" in user_input_str
        has_business = "企业" in user_input_str or "创业" in user_input_str
        
        if has_veteran and (has_individual_business or has_business):
            return {
                "step": "检索POLICY_A06",
                "content": "判断\"退役军人+创办企业\"可享受税收优惠政策，用户已提及退役军人身份和开汽车维修店，符合条件"
            }
        else:
            missing_conditions = []
            if not has_veteran:
                missing_conditions.append("退役军人身份")
            if not (has_individual_business or has_business):
                missing_conditions.append("创办企业")
            if missing_conditions:
                return {
                    "step": "检索POLICY_A06",
                    "content": f"判断\"退役军人+创办企业\"可享受税收优惠政策，用户未提及{', '.join(missing_conditions)}，需指出缺失条件"
                }
            else:
                return {
                    "step": "检索POLICY_A06",
                    "content": "判断\"退役军人+创办企业\"可享受税收优惠政策，用户已提及所有条件，符合条件"
                }
    
    def build_policy_substeps(self, relevant_policies, user_input, intent_info):
        """构建详细的政策分析子步骤"""
        policy_substeps = []
        # 检查用户是否提到带动就业
        user_input_str = user_input if isinstance(user_input, str) else str(user_input)
        has_employment = "带动就业" in user_input_str or "就业" in user_input_str or "带动" in user_input_str
        
        for policy in relevant_policies:
            policy_id = policy.get('policy_id', '')
            policy_title = policy.get('title', '')
            
            if policy_id == "POLICY_A03":
                # 返乡创业扶持补贴政策
                substep = self.analyze_policy_a03(user_input_str, has_employment)
            elif policy_id == "POLICY_A01":
                # 创业担保贷款贴息政策
                substep = self.analyze_policy_a01(user_input_str, intent_info)
            elif policy_id == "POLICY_A02":
                # 失业人员职业培训补贴政策
                substep = self.analyze_policy_a02(user_input_str)
            elif policy_id == "POLICY_A04":
                # 创业场地租金补贴政策
                substep = self.analyze_policy_a04(user_input_str)
            elif policy_id == "POLICY_A06":
                # 退役军人创业税收优惠政策
                substep = self.analyze_policy_a06(user_input_str)
            else:
                # 其他政策
                substep = {
                    "step": f"检索{policy_id}",
                    "content": f"分析{policy_title}的适用条件"
                }
            
            policy_substeps.append(substep)
        
        return policy_substeps
