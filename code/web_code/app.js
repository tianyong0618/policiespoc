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
    
    // 显示加载状态
    addMessageToHistory('ai', '正在处理您的问题...', true);

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
        
        // 添加AI回复到历史
        addStructuredMessageToHistory(data.response);
        
        // 检查是否命中缓存
        const isCacheHit = data.is_cache_hit || data.cache_hit || false;
        
        // 显示评估结果
        displayEvaluation(data.evaluation, data.execution_time, data.timing, data.llm_calls, isCacheHit);
        
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

// 添加结构化消息到历史
function addStructuredMessageToHistory(response) {
    const chatHistory = document.getElementById('chat-history');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ai structured';
    
    let content = '';
    
    if (response.positive) {
        content += `
            <div class="response-section positive">
                <h4>符合条件的政策</h4>
                <p>${response.positive}</p>
            </div>
        `;
    }
    
    if (response.negative) {
        content += `
            <div class="response-section negative">
                <h4>不符合条件的政策</h4>
                <p>${response.negative}</p>
            </div>
        `;
    }
    
    if (response.suggestions) {
        content += `
            <div class="response-section suggestions">
                <h4>主动建议</h4>
                <p>${response.suggestions}</p>
            </div>
        `;
    }
    
    messageDiv.innerHTML = `
        <div class="message-header">
            <span class="message-role">智能助手</span>
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