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

// 全局状态
let currentScenario = null;

// 初始化页面
document.addEventListener('DOMContentLoaded', function() {
    initEventListeners();
    loadUserProfile();
});

// 初始化事件监听
function initEventListeners() {
    // 场景卡片点击
    document.querySelectorAll('.scenario-card').forEach(card => {
        card.addEventListener('click', function() {
            const scenario = this.dataset.scenario;
            useScenario(scenario);
        });
    });

    // 发送按钮
    document.getElementById('send-btn').addEventListener('click', () => sendMessage());
    
    // 输入框回车发送
    document.getElementById('user-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // 新建对话
    document.getElementById('new-chat-btn').addEventListener('click', startNewChat);

    // 用户画像管理
    document.getElementById('profile-btn').addEventListener('click', openProfileModal);
    
    // 模态框关闭
    document.querySelectorAll('.close-btn, .close-btn-action').forEach(btn => {
        btn.addEventListener('click', closeProfileModal);
    });

    // 评估结果关闭
    document.querySelector('.toast-close').addEventListener('click', hideEvaluation);

    // 移动端菜单
    document.getElementById('menu-btn').addEventListener('click', toggleSidebar);
}

// 使用场景
function useScenario(scenario) {
    const scenarioInfo = SCENARIOS[scenario];
    if (scenarioInfo) {
        currentScenario = scenario;
        document.getElementById('user-input').value = scenarioInfo.example;
        sendMessage();
    }
}

// 开始新对话
function startNewChat() {
    document.getElementById('chat-history').innerHTML = '';
    document.getElementById('welcome-screen').style.display = 'flex';
    document.getElementById('user-input').value = '';
    currentScenario = null;
    hideEvaluation();
    
    // 移动端收起侧边栏
    if (window.innerWidth <= 768) {
        document.querySelector('.sidebar').classList.remove('active');
    }
}

// 发送消息
async function sendMessage() {
    const inputEl = document.getElementById('user-input');
    const userInput = inputEl.value.trim();
    if (!userInput) return;

    // 隐藏欢迎页
    document.getElementById('welcome-screen').style.display = 'none';

    // 添加用户消息
    addMessageToHistory('user', userInput);
    inputEl.value = '';

    // 添加加载状态
    const loadingId = addLoadingMessage();

    // 使用 SSE 流式请求
    try {
        const response = await fetch(`${API_BASE_URL}/chat/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: userInput,
                scenario: currentScenario || 'general'
            })
        });

        if (!response.ok) throw new Error('API请求失败');

        // 移除加载动画，准备接收流
        removeMessage(loadingId);
        
        // 创建一个新的消息气泡用于显示流式内容
        const messageId = 'msg-' + Date.now();
        const chatHistory = document.getElementById('chat-history');
        const messageContainer = document.createElement('div');
        messageContainer.className = 'message ai';
        messageContainer.id = messageId;
        
        // 构建新的 DOM 结构：思考区 + 回答区
        messageContainer.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content" style="width: 100%; background: transparent; padding: 0; box-shadow: none; border: none;">
                <!-- 思考折叠区 - 初始不添加 active 类 -->
                <div class="thinking-container">
                    <div class="thinking-header" onclick="toggleThinking(this)">
                        <span class="thinking-spinner"></span>
                        <span class="thinking-title">深度思考中...</span>
                        <span class="thinking-toggle-icon"></span>
                    </div>
                    <div class="thinking-content"></div>
                </div>
                <!-- 回答区 -->
                <div class="answer-content" style="background: transparent; padding: 12px 16px 12px 0; border: none; box-shadow: none;"></div>
            </div>
        `;
        chatHistory.appendChild(messageContainer);
        
        const thinkingContainer = messageContainer.querySelector('.thinking-container');
        const thinkingHeaderTitle = messageContainer.querySelector('.thinking-title');
        const thinkingSpinner = messageContainer.querySelector('.thinking-spinner');
        const thinkingContentEl = messageContainer.querySelector('.thinking-content');
        const answerContentEl = messageContainer.querySelector('.answer-content');

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        
        // 状态标记
        let isThinking = true; // 默认为思考模式
        let hasFinishedThinking = false;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');
            buffer = lines.pop(); // 保留最后一个不完整的块

            for (const line of lines) {
                if (line.startsWith('event: ')) {
                    const eventMatch = line.match(/^event: (.*)$/m);
                    const dataMatch = line.match(/^data: (.*)$/m);
                    
                    if (eventMatch && dataMatch) {
                        const event = eventMatch[1].trim();
                        const dataStr = dataMatch[1].trim();

                        if (event === 'context') {
                            const data = JSON.parse(dataStr);
                            // 显示推荐岗位
                            if (data.recommended_jobs && data.recommended_jobs.length > 0) {
                                displayRecommendedJobs(data.recommended_jobs);
                            }
                        } else if (event === 'message') {
                            const data = JSON.parse(dataStr);
                            let text = data.content || '';
                            
                            // 检测是否切换到结构化输出（回答部分）
                            // 匹配规则：Markdown 分割线 --- 或 **结构化输出** 或 【结构化输出】或 ### 结构化输出
                            // 移除 ^ 锚点，只要 chunk 中包含这些标记就触发切换，避免因分块导致的匹配失败
                            const structuredOutputRegex = /(---|(\*\*|【|###\s*)结构化输出(\*\*|】)?)/;
                            
                            if (isThinking && structuredOutputRegex.test(text)) {
                                isThinking = false;
                                hasFinishedThinking = true;
                                
                                // 更新思考区状态
                                thinkingContainer.classList.add('finished');
                                thinkingContainer.classList.remove('active'); // 默认收起
                                thinkingHeaderTitle.textContent = '已完成思考';
                                // 移除 spinner
                                if (thinkingSpinner) thinkingSpinner.style.display = 'none';
                                
                                // 清理 text 中的分割标记
                                text = text.replace(structuredOutputRegex, '');
                            }
                            
                            // 简单处理 Markdown 格式
                            let html = text
                                .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
                                .replace(/\n/g, '<br>');
                            
                            // 识别推荐岗位格式：推荐岗位：[JOB_A02] [职业技能培训讲师]
                            // 并转换为卡片样式
                            const jobRegex = /推荐岗位：\[(.*?)\]\s*\[(.*?)\]/g;
                            html = html.replace(jobRegex, (match, jobId, jobTitle) => {
                                return `
                                    <div class="job-card" style="margin: 12px 0; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; background: #fff; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                            <div style="font-weight: 600; color: #1e293b;">${jobTitle}</div>
                                            <div style="font-size: 12px; background: #eff6ff; color: #3b82f6; padding: 2px 6px; border-radius: 4px;">${jobId}</div>
                                        </div>
                                        <div style="font-size: 13px; color: #64748b;">点击查看详情 ></div>
                                    </div>
                                `;
                            });
                            
                            // 移除原有的结构化输出标题转换逻辑，因为现在它是分界线
                            if (html.includes('📑 结构化输出')) {
                                html = html.replace('📑 结构化输出', '');
                            }
                            
                            // 修复：如果分割线被过滤掉了，导致内容为空，就不添加空 span
                            if (!html.trim()) {
                                continue;
                            }

                            // 创建临时 span 追加
                            const span = document.createElement('span');
                            span.innerHTML = html;
                            
                            if (isThinking) {
                                // 过滤掉思考过程开头的空白字符
                                if (!thinkingContentEl.classList.contains('has-content')) {
                                    if (!text.trim()) {
                                        continue;
                                    }
                                    thinkingContentEl.classList.add('has-content');
                                    thinkingContainer.classList.add('active');
                                }
                                
                                // 过滤掉思考过程中完全不匹配的内容
                                // 比如有时候模型会输出 "根据..." 这种无意义的片段
                                // 这里可以根据实际情况增加更复杂的过滤逻辑
                                if (text.trim()) {
                                    thinkingContentEl.appendChild(span);
                                }
                            } else {
                                answerContentEl.appendChild(span);
                            }
                            
                            scrollToBottom();
                        } else if (event === 'done') {
                            console.log('Stream complete');
                            // 如果流结束了还在思考模式（没遇到分界线），强制结束思考
                            if (isThinking) {
                                thinkingContainer.classList.add('finished');
                                thinkingContainer.classList.remove('active');
                                thinkingHeaderTitle.textContent = '已完成思考';
                                if (thinkingSpinner) thinkingSpinner.style.display = 'none';
                                
                                // 兜底：如果整个返回都在思考区，说明没检测到分割线
                                // 此时尝试把思考区的内容复制一份到回答区，或者提示用户
                                if (answerContentEl.innerHTML.trim() === '') {
                                    // 简单处理：如果回答区为空，就保持思考区展开，方便查看
                                    thinkingContainer.classList.add('active'); 
                                    thinkingHeaderTitle.textContent = '思考完成 (未检测到结构化输出)';
                                }
                            }
                        } else if (event === 'error') {
                            console.error('Stream error:', dataStr);
                            answerContentEl.innerHTML += `<br><span style="color:red">错误: ${dataStr}</span>`;
                        }
                    }
                }
            }
        }

    } catch (error) {
        console.error(error);
        removeMessage(loadingId);
        addMessageToHistory('ai', '抱歉，服务暂时不可用，请稍后重试。');
    }
}

// 切换思考区折叠状态
function toggleThinking(header) {
    const container = header.parentElement;
    container.classList.toggle('active');
}

// 添加消息到历史
function addMessageToHistory(role, content) {
    const chatHistory = document.getElementById('chat-history');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const avatar = role === 'user' ? '👤' : '🤖';
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">${content}</div>
    `;
    
    chatHistory.appendChild(messageDiv);
    scrollToBottom();
    return messageDiv;
}

// 添加加载消息
function addLoadingMessage() {
    const id = 'loading-' + Date.now();
    const chatHistory = document.getElementById('chat-history');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ai loading';
    messageDiv.id = id;
    messageDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
        </div>
    `;
    chatHistory.appendChild(messageDiv);
    scrollToBottom();
    return id;
}

// 移除消息
function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// 显示思考过程
function displayThinkingProcess(steps) {
    const chatHistory = document.getElementById('chat-history');
    const container = document.createElement('div');
    container.className = 'message ai';
    
    let stepsHtml = steps.map((step, index) => `
        <div class="step-item">
            <div class="step-number">${index + 1}</div>
            <div class="step-content">
                <div>${step.step} <span class="step-status ${step.status}">${step.status === 'completed' ? '完成' : '进行中'}</span></div>
                <div style="font-size: 12px; color: #64748b; margin-top: 4px;">${step.content}</div>
            </div>
        </div>
    `).join('');

    container.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content" style="padding: 0; background: transparent; border: none; box-shadow: none;">
            <div class="thinking-process">
                <div class="thinking-header">
                    <span>🧠 思考过程</span>
                </div>
                <div class="thinking-steps">
                    ${stepsHtml}
                </div>
            </div>
        </div>
    `;
    
    chatHistory.appendChild(container);
    scrollToBottom();
}

// 显示结构化回答
function displayStructuredResponse(response) {
    if (!response || (!response.positive && !response.negative && !response.suggestions)) {
        return;
    }

    const chatHistory = document.getElementById('chat-history');
    const container = document.createElement('div');
    container.className = 'message ai';
    
    let contentHtml = '';
    
    if (response.positive) {
        contentHtml += `
            <div class="response-section positive">
                <h4>符合条件的政策</h4>
                <p>${response.positive}</p>
            </div>
        `;
    }
    
    if (response.negative) {
        contentHtml += `
            <div class="response-section negative">
                <h4>不符合条件的政策</h4>
                <p>${response.negative}</p>
            </div>
        `;
    }
    
    if (response.suggestions) {
        contentHtml += `
            <div class="response-section suggestions">
                <h4>主动建议</h4>
                <p>${response.suggestions}</p>
            </div>
        `;
    }

    container.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            ${contentHtml}
        </div>
    `;
    
    chatHistory.appendChild(container);
    scrollToBottom();
}

// 显示推荐岗位
function displayRecommendedJobs(jobs) {
    const chatHistory = document.getElementById('chat-history');
    const container = document.createElement('div');
    container.className = 'message ai';
    
    let jobsHtml = jobs.map(job => `
        <div class="job-card">
            <div class="job-header">
                <div class="job-title">
                    <span class="id-badge">${job.job_id || 'ID未知'}</span>
                    ${job.title}
                </div>
                <div class="job-salary">${job.salary}</div>
            </div>
            <div class="job-details">
                <p>📍 ${job.location} | 📋 ${job.requirements.slice(0, 2).join('、')}...</p>
                <p>✨ ${job.features}</p>
            </div>
        </div>
    `).join('');

    container.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content" style="background: transparent; border: none; box-shadow: none; padding: 0;">
            <div class="jobs-container">
                ${jobsHtml}
            </div>
        </div>
    `;
    
    chatHistory.appendChild(container);
    scrollToBottom();
}

// 显示评估结果
function showEvaluation(evaluation, time) {
    const toast = document.getElementById('evaluation-toast');
    const content = document.getElementById('evaluation-content');
    
    content.innerHTML = `
        <div class="eval-item">
            <span class="eval-label">政策召回准确率</span>
            <span class="eval-value">${evaluation.policy_recall_accuracy}</span>
        </div>
        <div class="eval-item">
            <span class="eval-label">条件判断准确率</span>
            <span class="eval-value">${evaluation.condition_accuracy}</span>
        </div>
        <div class="eval-item">
            <span class="eval-label">响应时间</span>
            <span class="eval-value">${time ? time.toFixed(2) + 's' : 'N/A'}</span>
        </div>
    `;
    
    toast.classList.add('show');
    
    // 5秒后自动隐藏
    setTimeout(hideEvaluation, 5000);
}

function hideEvaluation() {
    document.getElementById('evaluation-toast').classList.remove('show');
}

// 滚动到底部
function scrollToBottom() {
    const container = document.getElementById('chat-container');
    container.scrollTop = container.scrollHeight;
}

// 用户画像模态框控制
function openProfileModal() {
    document.getElementById('profile-modal').classList.add('active');
    loadUserProfile();
}

function closeProfileModal() {
    document.getElementById('profile-modal').classList.remove('active');
}

// 侧边栏控制
function toggleSidebar() {
    document.querySelector('.sidebar').classList.toggle('active');
}

// 加载用户画像
async function loadUserProfile() {
    try {
        const response = await fetch(`${API_BASE_URL}/users/USER001/profile`);
        if (response.ok) {
            const profile = await response.json();
            fillProfileForm(profile);
        }
    } catch (error) {
        console.error('加载画像失败', error);
    }
}

// 填充表单
function fillProfileForm(profile) {
    if (profile.user_id) {
        const badge = document.getElementById('profile-id-badge');
        badge.textContent = profile.user_id;
        badge.classList.remove('hidden');
    }
    
    const info = profile.basic_info || {};
    document.getElementById('age').value = info.age || '';
    document.getElementById('gender').value = info.gender || '';
    document.getElementById('education').value = info.education || '';
    document.getElementById('work_experience').value = info.work_experience || '';
    
    document.getElementById('skills').value = (profile.skills || []).join(', ');
    
    const prefs = profile.preferences || {};
    document.getElementById('salary_range').value = (prefs.salary_range || []).join(', ');
    document.getElementById('work_location').value = (prefs.work_location || []).join(', ');
    
    document.getElementById('policy_interest').value = (profile.policy_interest || []).join(', ');
    document.getElementById('job_interest').value = (profile.job_interest || []).join(', ');
}

// 保存用户画像
async function saveUserProfile() {
    const data = {
        basic_info: {
            age: document.getElementById('age').value,
            gender: document.getElementById('gender').value,
            education: document.getElementById('education').value,
            work_experience: document.getElementById('work_experience').value
        },
        skills: document.getElementById('skills').value.split(/[,，]/).map(s => s.trim()).filter(Boolean),
        preferences: {
            salary_range: document.getElementById('salary_range').value.split(/[,，]/).map(s => s.trim()).filter(Boolean),
            work_location: document.getElementById('work_location').value.split(/[,，]/).map(s => s.trim()).filter(Boolean)
        },
        policy_interest: document.getElementById('policy_interest').value.split(/[,，]/).map(s => s.trim()).filter(Boolean),
        job_interest: document.getElementById('job_interest').value.split(/[,，]/).map(s => s.trim()).filter(Boolean)
    };

    try {
        const response = await fetch(`${API_BASE_URL}/users/USER001/profile`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            closeProfileModal();
            alert('用户画像保存成功');
        } else {
            alert('保存失败');
        }
    } catch (error) {
        console.error('保存失败', error);
        alert('保存失败');
    }
}
