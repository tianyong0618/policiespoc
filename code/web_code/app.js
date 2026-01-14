// API基础URL
const API_BASE_URL = 'http://localhost:8000/api';

// 场景配置
const SCENARIOS = {
    scenario1: {
        name: "创业扶持政策精准咨询",
        example: "我是去年从广东回来的农民工，想在家开个小加工厂（小微企业），听说有返乡创业补贴，能领2万吗？另外创业贷款怎么申请？"
    },
    scenario2: {
        name: "技能培训岗位个性化推荐",
        example: "请为一位32岁、失业、持有中级电工证的女性推荐工作，她关注补贴申领和灵活时间。"
    },
    scenario3: {
        name: "多重政策叠加咨询",
        example: "我是退役军人，开汽车维修店（个体），同时入驻创业孵化基地（年租金8000元），能同时享受税收优惠和场地补贴吗？"
    }
};

// 初始化页面
document.addEventListener('DOMContentLoaded', function() {
    // 绑定场景按钮事件
    document.querySelectorAll('.scenario-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const scenario = this.dataset.scenario;
            useScenario(scenario);
        });
    });

    // 绑定发送按钮事件
    document.getElementById('send-btn').addEventListener('click', sendMessage);
    
    // 绑定回车键发送
    document.getElementById('user-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // 绑定清空历史按钮事件
    document.getElementById('clear-btn').addEventListener('click', clearHistory);
});

// 使用场景
function useScenario(scenario) {
    const scenarioInfo = SCENARIOS[scenario];
    if (scenarioInfo) {
        document.getElementById('user-input').value = scenarioInfo.example;
        sendMessage(scenario);
    }
}

// 发送消息
async function sendMessage(scenario) {
    // 如果scenario是对象（可能是事件对象），则使用默认值'general'
    if (typeof scenario === 'object') {
        scenario = 'general';
    }
    const userInput = document.getElementById('user-input').value.trim();
    if (!userInput) return;

    // 移除欢迎消息
    const welcomeMessage = document.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }

    // 添加用户消息到历史
    addMessageToHistory('user', userInput);
    
    // 清空输入框
    document.getElementById('user-input').value = '';
    
    // 移除之前的加载消息（如果有）
    removeLoadingMessage();
    
    // 添加新的加载消息，显示为"正在分析您的问题..."
    addMessageToHistory('ai', '正在分析您的问题...', true);

    try {
        // 构建请求数据
        const requestData = {
            message: userInput,
            scenario: scenario
        };
        
        console.log('发送请求:', requestData);
        
        // 调用API
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });

        console.log('响应状态:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('API错误:', errorText);
            throw new Error(`API调用失败: ${response.status} ${errorText}`);
        }

        const data = await response.json();
        console.log('响应数据:', data);
        
        // 移除加载消息
        removeLoadingMessage();
        
        // 按照思考过程的顺序，逐步显示每个步骤
        if (data.thinking_process && data.thinking_process.length > 0) {
            // 首先显示"思考过程"标题
            const chatHistory = document.getElementById('chat-history');
            const thinkingDiv = document.createElement('div');
            thinkingDiv.className = 'message ai thinking-process';
            thinkingDiv.innerHTML = `
                <div class="message-header">
                    <span class="message-role">智能助手</span>
                    <span class="thinking-badge">思考过程</span>
                </div>
                <div class="message-content">
                    <div class="thinking-steps">
                    </div>
                </div>
            `;
            chatHistory.appendChild(thinkingDiv);
            chatHistory.scrollTop = chatHistory.scrollHeight;
            
            const stepsContainer = thinkingDiv.querySelector('.thinking-steps');
            
            // 逐个步骤显示思考过程
            for (let i = 0; i < data.thinking_process.length; i++) {
                const step = data.thinking_process[i];
                
                // 创建步骤元素
                const stepDiv = document.createElement('div');
                stepDiv.className = `thinking-step ${step.status}`;
                stepDiv.innerHTML = `
                    <div class="step-header">
                        <span class="step-number">${i + 1}</span>
                        <span class="step-title">${step.step}</span>
                        <span class="step-status ${step.status}">${step.status === 'completed' ? '完成' : '进行中'}</span>
                    </div>
                    <div class="step-content">
                        <span class="typing-text"></span>
                        <span class="typing-cursor">|</span>
                    </div>
                `;
                stepsContainer.appendChild(stepDiv);
                chatHistory.scrollTop = chatHistory.scrollHeight;
                
                // 逐字显示步骤内容
                const typingText = stepDiv.querySelector('.typing-text');
                const typingCursor = stepDiv.querySelector('.typing-cursor');
                
                for (let j = 0; j < step.content.length; j++) {
                    typingText.textContent += step.content.charAt(j);
                    chatHistory.scrollTop = chatHistory.scrollHeight;
                    await new Promise(resolve => setTimeout(resolve, 30)); // 打字速度
                }
                
                // 移除光标
                typingCursor.remove();
                
                // 步骤之间的延迟
                await new Promise(resolve => setTimeout(resolve, 500));
            }
        }
        
        // 显示结构化回答
        if (data.response) {
            // 创建回答容器
            const chatHistory = document.getElementById('chat-history');
            const responseDiv = document.createElement('div');
            responseDiv.className = 'message ai structured';
            responseDiv.innerHTML = `
                <div class="message-header">
                    <span class="message-role">智能助手</span>
                </div>
                <div class="message-content">
                </div>
            `;
            chatHistory.appendChild(responseDiv);
            chatHistory.scrollTop = chatHistory.scrollHeight;
            
            const contentContainer = responseDiv.querySelector('.message-content');
            
            // 按照顺序显示各个部分
            const sections = [];
            
            if (data.response.negative) {
                sections.push({
                    type: 'negative',
                    title: '不符合条件的政策',
                    content: data.response.negative
                });
            }
            
            if (data.response.positive) {
                sections.push({
                    type: 'positive',
                    title: '符合条件的政策',
                    content: data.response.positive
                });
            }
            
            if (data.response.suggestions) {
                sections.push({
                    type: 'suggestions',
                    title: '主动建议',
                    content: data.response.suggestions
                });
            }
            
            for (let i = 0; i < sections.length; i++) {
                const section = sections[i];
                
                // 创建部分元素
                const sectionDiv = document.createElement('div');
                sectionDiv.className = `response-section ${section.type}`;
                sectionDiv.innerHTML = `
                    <h4>${section.title}</h4>
                    <p>
                        <span class="typing-text"></span>
                        <span class="typing-cursor">|</span>
                    </p>
                `;
                contentContainer.appendChild(sectionDiv);
                chatHistory.scrollTop = chatHistory.scrollHeight;
                
                // 逐字显示部分内容
                const typingText = sectionDiv.querySelector('.typing-text');
                const typingCursor = sectionDiv.querySelector('.typing-cursor');
                
                for (let j = 0; j < section.content.length; j++) {
                    typingText.textContent += section.content.charAt(j);
                    chatHistory.scrollTop = chatHistory.scrollHeight;
                    await new Promise(resolve => setTimeout(resolve, 30)); // 打字速度
                }
                
                // 移除光标
                typingCursor.remove();
                
                // 部分之间的延迟
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
        }
        
        // 显示评估结果
        displayEvaluation(data.evaluation, data.execution_time, data.timing, data.llm_calls, data.is_cache_hit || data.cache_hit || false);
        
    } catch (error) {
        console.error('发送消息错误:', error);
        
        // 移除加载消息
        removeLoadingMessage();
        
        // 添加错误消息
        addMessageToHistory('ai', `抱歉，处理您的问题时出错：${error.message}`);
    }
}

// 添加消息到历史
function addMessageToHistory(role, content, isLoading = false) {
    const chatHistory = document.getElementById('chat-history');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role} ${isLoading ? 'loading' : ''}`;
    
    if (isLoading) {
        messageDiv.id = 'loading-message';
        content = '<div class="loading-spinner"></div>' + content;
    }
    
    messageDiv.innerHTML = `
        <div class="message-header">
            <span class="message-role">${role === 'user' ? '您' : '智能助手'}</span>
        </div>
        <div class="message-content">${content}</div>
    `;
    
    chatHistory.appendChild(messageDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}



// 移除加载消息
function removeLoadingMessage() {
    const loadingMessage = document.getElementById('loading-message');
    if (loadingMessage) {
        loadingMessage.remove();
    }
}



// 清空历史
function clearHistory() {
    const chatHistory = document.getElementById('chat-history');
    chatHistory.innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">👋</div>
            <div class="welcome-text">
                <h3>欢迎使用政策咨询智能体</h3>
                <p>选择上方场景或直接输入您的问题，我将为您提供精准的政策咨询建议。</p>
            </div>
        </div>
    `;
    
    const evaluationResult = document.getElementById('evaluation-result');
    evaluationResult.innerHTML = `
        <div class="evaluation-placeholder">
            <div class="placeholder-icon">📊</div>
            <p>请先发送问题以查看评估结果</p>
        </div>
    `;
}

// 显示评估结果
function displayEvaluation(evaluation, executionTime, timing, llmCalls, isCacheHit = false) {
    const evaluationResult = document.getElementById('evaluation-result');
    
    // 构建模型调用时间的HTML
    let llmCallsHtml = '';
    
    if (isCacheHit) {
        // 缓存命中，显示使用缓存提示
        llmCallsHtml = `
            <div class="evaluation-item cache-hit">
                <span class="label">模型调用时间：</span>
                <span class="value cache-badge">⚡ 使用缓存 (0.00秒)</span>
            </div>
        `;
    } else if (llmCalls && llmCalls.length > 0) {
        // 正常调用，显示各模型调用时间
        llmCalls.forEach((call, index) => {
            llmCallsHtml += `
                <div class="evaluation-item">
                    <span class="label">模型调用时间${index + 1}（${call.type}）：</span>
                    <span class="value">${call.time ? call.time.toFixed(2) : 'N/A'}秒</span>
                </div>
            `;
        });
    } else {
        // 使用timing.combined
        llmCallsHtml = `
            <div class="evaluation-item">
                <span class="label">模型调用时间：</span>
                <span class="value">${timing ? timing.combined ? timing.combined.toFixed(2) : 'N/A' : 'N/A'}秒</span>
            </div>
        `;
    }
    
    evaluationResult.innerHTML = `
        <div class="evaluation-content">
            ${isCacheHit ? `
                <div class="cache-notice">
                    <span class="cache-icon">💾</span>
                    <span>本次查询命中缓存，直接返回历史结果</span>
                </div>
            ` : ''}
            <div class="evaluation-item">
                <span class="label">政策条款召回准确率：</span>
                <span class="value">${evaluation.policy_recall_accuracy}</span>
            </div>
            <div class="evaluation-item">
                <span class="label">条件判断准确率：</span>
                <span class="value">${evaluation.condition_accuracy}</span>
            </div>
            ${llmCallsHtml}
            <div class="evaluation-item">
                <span class="label">最终响应时间：</span>
                <span class="value">${executionTime ? executionTime.toFixed(2) : 'N/A'}秒</span>
            </div>
        </div>
    `;
}