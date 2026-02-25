// API基础URL - 自动适配环境
const API_BASE_URL = (() => {
  // 检测当前环境
  const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  // 本地开发使用完整URL，部署后使用相对路径
  return isLocal ? 'http://127.0.0.1:8000/api' : '/api';
})();

// 版本号，用于强制刷新缓存
const APP_VERSION = '1.0.1';

// 全局状态
let currentSessionId = null;
let eventSource = null;
let isStreaming = false;

// 初始化页面
document.addEventListener('DOMContentLoaded', function() {
    initEventListeners();
    loadUserProfile();
    loadHistoryList();
});

// 初始化事件监听
function initEventListeners() {
    console.log('初始化事件监听');
    
    // 发送按钮
    const sendBtn = document.getElementById('send-btn');
    console.log('发送按钮元素:', sendBtn);
    if (sendBtn) {
        sendBtn.addEventListener('click', () => {
            console.log('发送按钮被点击');
            sendMessage();
        });
    }
    
    // 输入框回车发送
    const userInput = document.getElementById('user-input');
    console.log('用户输入框元素:', userInput);
    if (userInput) {
        userInput.addEventListener('keypress', function(e) {
            console.log('输入框按键:', e.key);
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                console.log('回车发送');
                sendMessage();
            }
        });
    }

    // 新建对话
    const newChatBtn = document.getElementById('new-chat-btn');
    console.log('新建对话按钮元素:', newChatBtn);
    if (newChatBtn) {
        newChatBtn.addEventListener('click', startNewChat);
    }

    // 模态框关闭
    document.querySelectorAll('.close-btn, .close-btn-action').forEach(btn => {
        btn.addEventListener('click', closeProfileModal);
    });

    // 评估结果关闭
    const toastClose = document.querySelector('.toast-close');
    console.log('评估结果关闭按钮元素:', toastClose);
    if (toastClose) {
        toastClose.addEventListener('click', hideEvaluation);
    }

    // 历史记录列表事件委托
    const historyList = document.querySelector('.history-list');
    console.log('历史记录列表元素:', historyList);
    if (historyList) {
        historyList.addEventListener('click', function(e) {
            // 处理删除按钮点击
            const deleteBtn = e.target.closest('.delete-icon');
            if (deleteBtn) {
                e.preventDefault();
                e.stopPropagation();
                const sessionId = deleteBtn.dataset.sessionId;
                deleteSession(sessionId);
                return;
            }

            // 处理会话项点击
            const historyItem = e.target.closest('.history-item');
            if (historyItem) {
                // 如果点击的是删除按钮，不处理（理论上上面的 deleteBtn 判断已经拦截了，双重保险）
                if (e.target.closest('.delete-icon')) return;

                const sessionId = historyItem.dataset.sessionId;
                loadSession(sessionId);
            }
        });
    }
}

// 加载历史会话列表
async function loadHistoryList() {
    try {
        const response = await fetch(`${API_BASE_URL}/history`);
        if (!response.ok) return;
        
        const data = await response.json();
        const historyList = document.querySelector('.history-list');
        
        if (data.sessions && data.sessions.length > 0) {
            historyList.innerHTML = data.sessions.map(session => `
                <div class="history-item ${session.id === currentSessionId ? 'active' : ''}" data-session-id="${session.id}">
                    <span class="icon">💬</span>
                    <span class="text">${session.title || '新对话'}</span>
                    <span class="delete-icon" data-session-id="${session.id}" title="删除">×</span>
                </div>
            `).join('');
            
            // 如果当前有选中的会话，同步更新顶部标题
            if (currentSessionId) {
                const currentSession = data.sessions.find(s => s.id === currentSessionId);
                if (currentSession) {
                    updateChatTitle(currentSession.title || '新对话');
                }
            }
        } else {
            historyList.innerHTML = '<div style="padding: 10px; color: #94a3b8; font-size: 13px; text-align: center;">暂无历史记录</div>';
        }
    } catch (error) {
        console.error('加载历史记录失败:', error);
        const historyList = document.querySelector('.history-list');
        historyList.innerHTML = '<div style="padding: 10px; color: #94a3b8; font-size: 13px; text-align: center;">暂无历史记录</div>';
    }
}

// 加载特定会话
async function loadSession(sessionId) {
    if (currentSessionId === sessionId) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/history/${sessionId}`);
        if (!response.ok) throw new Error('加载会话失败');
        
        const session = await response.json();
        currentSessionId = sessionId;
        
        // 更新标题
        updateChatTitle(session.title || '新对话');
        
        // 更新侧边栏激活状态
        document.querySelectorAll('.history-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.sessionId === sessionId) {
                item.classList.add('active');
            }
        });
        
        // 隐藏欢迎页，显示聊天记录
        document.getElementById('welcome-screen').style.display = 'none';
        const chatHistory = document.getElementById('chat-history');
        chatHistory.innerHTML = '';
        
        // 渲染消息
        if (session.messages && session.messages.length > 0) {
            session.messages.forEach(msg => {
                if (msg.role === 'user') {
                    addMessageToHistory('user', msg.content);
                } else if (msg.role === 'ai') {
                    // AI消息可能包含JSON数据，需要解析
                    try {
                        const data = JSON.parse(msg.content);
                        renderAnalysisResult(data);
                    } catch (e) {
                        // 如果不是JSON，直接显示
                        addMessageToHistory('ai', msg.content);
                    }
                }
            });
        }
        
        // 确保滚动到底部
        setTimeout(scrollToBottom, 100);
        
        // 移动端收起侧边栏
        if (window.innerWidth <= 768) {
            document.querySelector('.sidebar').classList.remove('active');
        }
        
    } catch (error) {
        console.error('加载会话详情失败:', error);
    }
}

// 删除会话
async function deleteSession(sessionId) {
    console.log('Attempting to delete session:', sessionId);
    console.log('Current history list HTML before confirm:', document.querySelector('.history-list').innerHTML);
    
    // 如果用户点击取消，不执行删除
    if (!confirm('确定要删除这条对话吗？')) {
        console.log('Delete cancelled by user');
        return; 
    }
    
    console.log('User confirmed delete');
    console.log('History list HTML after confirm:', document.querySelector('.history-list').innerHTML);
    
    // 找到对应的DOM元素（在用户确认后）
    const historyItem = document.querySelector(`.history-item[data-session-id="${sessionId}"]`);
    
    // 乐观更新：先在界面上移除（或添加删除中的样式）
    if (historyItem) {
        historyItem.style.opacity = '0.5'; // 变淡表示处理中
        historyItem.style.pointerEvents = 'none'; // 防止重复点击
    }

    try {
        await fetch(`${API_BASE_URL}/history/${sessionId}`, { method: 'DELETE' });
        console.log('Delete API call succeeded');
        if (currentSessionId === sessionId) {
            startNewChat();
        }
        loadHistoryList(); // 重新加载列表，这会彻底移除该项
    } catch (error) {
        console.error('删除会话失败:', error);
        // 如果失败，恢复样式
        if (historyItem) {
            historyItem.style.opacity = '1';
            historyItem.style.pointerEvents = 'auto';
        }
        alert('删除失败，请稍后重试');
    }
}

// 添加消息到历史记录
function addMessageToHistory(role, content) {
    const chatHistory = document.getElementById('chat-history');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${role === 'user' ? '👤' : '🤖'}</div>
        <div class="message-content">${content}</div>
    `;
    
    chatHistory.appendChild(messageDiv);
    scrollToBottom();
}

// 开始新对话
function startNewChat() {
    currentSessionId = null;
    document.getElementById('chat-history').innerHTML = '';
    document.getElementById('welcome-screen').style.display = 'flex';
    document.getElementById('user-input').value = '';
    updateChatTitle('政策咨询助手'); // 重置标题
    hideEvaluation();
    
    // 更新侧边栏选中状态
    document.querySelectorAll('.history-item').forEach(item => item.classList.remove('active'));
    
    // 移动端收起侧边栏
    if (window.innerWidth <= 768) {
        document.querySelector('.sidebar').classList.remove('active');
    }
}

// 开始对话（从欢迎页）
function startConversation() {
    document.getElementById('welcome-screen').style.display = 'none';
    document.getElementById('user-input').focus();
}

// 开始对话并自动发送查询
function startConversationWithQuery(query) {
    document.getElementById('welcome-screen').style.display = 'none';
    document.getElementById('user-input').value = query;
    document.getElementById('user-input').focus();
    sendMessage();
}

// 统一更新标题函数
function updateChatTitle(title) {
    // 更新移动端标题
    const mobileTitle = document.querySelector('.chat-window-title');
    if (mobileTitle) {
        mobileTitle.textContent = title;
    }
}

// 发送消息
async function sendMessage() {
    console.log('发送消息函数被调用');
    const userInput = document.getElementById('user-input').value.trim();
    console.log('用户输入:', userInput);
    if (!userInput) return;
    
    // 隐藏欢迎页
    document.getElementById('welcome-screen').style.display = 'none';
    
    // 添加用户消息到历史记录
    addMessageToHistory('user', userInput);
    
    // 清空输入框
    document.getElementById('user-input').value = '';
    
    // 禁用发送按钮，防止重复发送
    const sendBtn = document.getElementById('send-btn');
    sendBtn.disabled = true;
    
    try {
        // 发送请求到流式API
        const requestBody = {
            message: userInput
        };
        // 只有当currentSessionId不为null时才发送该字段
        if (currentSessionId) {
            requestBody.session_id = currentSessionId;
        }
        console.log('发送请求到:', `${API_BASE_URL}/chat/stream`);
        console.log('请求体:', requestBody);
        const response = await fetch(`${API_BASE_URL}/chat/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        console.log('响应状态:', response.status);
        if (!response.ok) {
            throw new Error('API请求失败');
        }
        
        // 处理流式响应
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let thinkingElement = null;
        
        // 创建AI消息容器
        const chatHistory = document.getElementById('chat-history');
        const aiMessageDiv = document.createElement('div');
        aiMessageDiv.className = 'message ai';
        chatHistory.appendChild(aiMessageDiv);
        
        // 处理流数据
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            console.log('收到流数据:', buffer);
            
            // 处理完整的事件
            const lines = buffer.split('\n\n');
            console.log('分割后的行:', lines);
            for (let i = 0; i < lines.length - 1; i++) {
                const line = lines[i];
                if (!line) continue;
                
                try {
                    // 解析SSE事件
                    const eventMatch = line.match(/^event: (\w+)$/m);
                    const dataMatch = line.match(/^data: (.*)$/ms);
                    
                    console.log('事件匹配:', eventMatch);
                    console.log('数据匹配:', dataMatch);
                    
                    if (eventMatch && dataMatch) {
                        const eventType = eventMatch[1];
                        const data = JSON.parse(dataMatch[1]);
                        
                        console.log('收到事件:', eventType, data);
                        
                        // 处理不同类型的事件
                        switch (eventType) {
                            case 'session':
                                // 保存会话ID
                                currentSessionId = data.session_id;
                                loadHistoryList();
                                break;
                                
                            case 'follow_up':
                                // 显示追问
                                renderFollowUp(data, aiMessageDiv);
                                break;
                                
                            case 'analysis_start':
                                // 显示分析开始，添加更明显的加载动画
                                // 只有当还没有任何思考过程时才显示加载动画
                                if (!thinkingElement && !aiMessageDiv.querySelector('.thinking-container')) {
                                    aiMessageDiv.innerHTML = `
                                        <div class="message-avatar">🤖</div>
                                        <div class="message-content">
                                            <div class="thinking-container active">
                                                <div class="thinking-header">
                                                    <span class="thinking-title">正在分析...</span>
                                                    <span class="thinking-toggle-icon"></span>
                                                </div>
                                                <div class="thinking-content">
                                                    <div class="loading-indicator">
                                                        <div class="typing-dots">
                                                            <div class="typing-dot"></div>
                                                            <div class="typing-dot"></div>
                                                            <div class="typing-dot"></div>
                                                        </div>
                                                        <div class="loading-text">正在分析您的需求，请稍候...</div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    `;
                                }
                                scrollToBottom();
                                break;
                                
                            case 'thinking':
                                // 显示思考过程 - 流式动态显示
                                console.log('收到thinking事件:', data);
                                
                                // 确保aiMessageDiv有message-content元素
                                if (!aiMessageDiv.querySelector('.message-content')) {
                                    // 如果message-content不存在，重新创建整个结构
                                    aiMessageDiv.innerHTML = `
                                        <div class="message-avatar">🤖</div>
                                        <div class="message-content">
                                        </div>
                                    `;
                                }
                                
                                // 确保有思考过程容器
                                if (!thinkingElement) {
                                    // 检查是否已经有思考过程容器
                                    let thinkingContainer = aiMessageDiv.querySelector('.thinking-container');
                                    if (!thinkingContainer) {
                                        // 创建思考过程容器
                                        thinkingContainer = document.createElement('div');
                                        thinkingContainer.className = 'thinking-container active';
                                        thinkingContainer.innerHTML = `
                                            <div class="thinking-header">
                                                <span class="thinking-title">思考过程</span>
                                                <span class="thinking-toggle-icon" style="transform: rotate(180deg);"></span>
                                            </div>
                                            <div class="thinking-content has-content"></div>
                                        `;
                                        aiMessageDiv.querySelector('.message-content').appendChild(thinkingContainer);
                                        // 添加点击事件
                                        if (thinkingContainer.querySelector('.thinking-header')) {
                                            thinkingContainer.querySelector('.thinking-header').addEventListener('click', function() {
                                                thinkingContainer.classList.toggle('active');
                                            });
                                        }
                                    }
                                    thinkingElement = thinkingContainer.querySelector('.thinking-content');
                                }
                                
                                // 流式添加思考内容，使用打字机效果
                                if (thinkingElement) {
                                    console.log('添加思考内容:', data.content);
                                    // 为每个思考步骤创建一个新的元素
                                    const stepElement = document.createElement('div');
                                    stepElement.className = 'thinking-step';
                                    thinkingElement.appendChild(stepElement);
                                    
                                    // 实现打字机效果
                                    const content = data.content;
                                    let index = 0;
                                    const typingSpeed = 30; // 打字速度（毫秒/字符）
                                    
                                    console.log('开始打字机效果，内容长度:', content.length);
                                    
                                    function typeWriter() {
                                        if (index < content.length) {
                                            console.log('打字机效果：添加字符:', content.charAt(index));
                                            stepElement.textContent += content.charAt(index);
                                            index++;
                                            setTimeout(typeWriter, typingSpeed);
                                            scrollToBottom();
                                        } else {
                                            console.log('打字机效果完成');
                                        }
                                    }
                                    
                                    // 立即开始打字机效果
                                    typeWriter();
                                } else {
                                    console.log('thinkingElement不存在');
                                }
                                break;
                                
                            case 'analysis_result':
                                // 显示分析结果，移除之前的简单思考过程容器，只保留详细的思考过程
                                console.log('渲染分析结果:', data);
                                // 检查data是否是字符串，如果是则解析为JSON
                                if (typeof data === 'string') {
                                    try {
                                        data = JSON.parse(data);
                                        console.log('解析后的data:', data);
                                    } catch (error) {
                                        console.error('解析data失败:', error);
                                    }
                                }
                                renderAnalysisResult(data, aiMessageDiv);
                                break;
                                
                            case 'analysis_complete':
                                // 分析完成，更新思考过程状态
                                const thinkingContainer = aiMessageDiv.querySelector('.thinking-container');
                                if (thinkingContainer) {
                                    thinkingContainer.classList.add('finished');
                                }
                                break;
                                
                            case 'error':
                                // 显示错误
                                aiMessageDiv.innerHTML = `
                                    <div class="message-avatar">🤖</div>
                                    <div class="message-content">
                                        <div class="error-message">
                                            <span>❌</span>
                                            ${data.error}
                                        </div>
                                    </div>
                                `;
                                scrollToBottom();
                                break;
                        }
                    }
                } catch (error) {
                    console.error('处理流式事件失败:', error);
                    console.error('出错的行:', line);
                    // 继续处理下一个事件
                }
            }
            
            // 保留未处理的部分
            buffer = lines[lines.length - 1];
        }
        
    } catch (error) {
        console.error('发送消息失败:', error);
        // 显示错误消息
        const chatHistory = document.getElementById('chat-history');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'message ai';
        errorDiv.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content">
                <div class="error-message">
                    <span>❌</span>
                    处理请求失败，请稍后重试
                </div>
            </div>
        `;
        chatHistory.appendChild(errorDiv);
    } finally {
        // 启用发送按钮
        sendBtn.disabled = false;
        scrollToBottom();
    }
}

// 渲染追问
function renderFollowUp(data, container) {
    container.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <div class="follow-up-card">
                <div class="follow-up-header">
                    <span>💭</span>
                    需要更多信息
                </div>
                <div class="follow-up-content">
                    ${data.content || data.question || '请提供更多信息'}
                </div>
            </div>
        </div>
    `;
    
    scrollToBottom();
    // 自动聚焦到输入框，方便用户直接输入回答
    document.getElementById('user-input').focus();
}

// 渲染分析结果
function renderAnalysisResult(data, container) {
    if (!container) {
        const chatHistory = document.getElementById('chat-history');
        container = document.createElement('div');
        container.className = 'message ai';
        chatHistory.appendChild(container);
    }
    
    // 检查数据结构，适配后端返回的格式
    let positiveContent = '';
    let negativeContent = '';
    let suggestionsContent = '';
    let relevantPolicies = [];
    let thinkingProcess = [];
    let recommendedJobs = [];
    let recommendedCourses = [];
    let answerContent = '';
    let intentData = null;
    
    console.log('分析结果数据:', data);
    
    // 处理SSE事件格式（从历史记录加载时）
    if (data.type === 'analysis_result') {
        console.log('处理analysis_result格式数据:', data);
        // 保持data不变，因为thinking_process等字段在根级别
    }
    
    // 处理analysis_result事件格式
    if (data.type === 'analysis_result') {
        // 从response字段中获取数据
        if (data.response) {
            positiveContent = data.response.positive || '';
            negativeContent = data.response.negative || '';
            suggestionsContent = data.response.suggestions || '';
            answerContent = data.response.answer || '';
        }
        intentData = data.intent || null;
        relevantPolicies = data.relevant_policies || [];
        thinkingProcess = data.thinking_process || [];
        recommendedJobs = data.recommended_jobs || [];
        recommendedCourses = data.recommended_courses || [];
    } else if (data.content) {
        // 后端返回的流式响应格式
        positiveContent = data.content.positive || '';
        negativeContent = data.content.negative || '';
        suggestionsContent = data.content.suggestions || '';
        answerContent = data.content.answer || '';
        intentData = data.content.intent || data.intent || null;
        relevantPolicies = data.relevant_policies || [];
        thinkingProcess = data.thinking_process || [];
        recommendedJobs = data.recommended_jobs || [];
        recommendedCourses = data.recommended_courses || [];
    } else if (data.positive !== undefined || data.negative !== undefined || data.suggestions !== undefined || data.answer !== undefined) {
        // 直接返回的分析结果格式
        positiveContent = data.positive || '';
        negativeContent = data.negative || '';
        suggestionsContent = data.suggestions || '';
        answerContent = data.answer || '';
        intentData = data.intent || null;
        relevantPolicies = data.relevant_policies || [];
        thinkingProcess = data.thinking_process || [];
        recommendedJobs = data.recommended_jobs || [];
        recommendedCourses = data.recommended_courses || [];
    }
    
    // 处理空数组情况
    if (Array.isArray(positiveContent)) positiveContent = '';
    if (Array.isArray(negativeContent)) negativeContent = '';
    if (Array.isArray(suggestionsContent)) suggestionsContent = '';
    
    console.log('处理后的数据:', {
        positiveContent,
        negativeContent,
        suggestionsContent,
        answerContent,
        intentData,
        relevantPolicies,
        thinkingProcess,
        recommendedJobs,
        recommendedCourses
    });
    
    // 生成动态主动建议
    let dynamicSuggestions = '';
    const suggestions = [];
    
    // 加载岗位数据
    let jobsData = [
        {"job_id": "JOB_A01", "title": "创业孵化基地管理员", "policy_relations": ["POLICY_A01", "POLICY_A03", "POLICY_A04"]},
        {"job_id": "JOB_A02", "title": "职业技能培训讲师", "policy_relations": ["POLICY_A02"]},
        {"job_id": "JOB_A03", "title": "电商创业辅导专员", "policy_relations": ["POLICY_A04"]},
        {"job_id": "JOB_A04", "title": "技能培训课程顾问", "policy_relations": ["POLICY_A02", "POLICY_A05"]},
        {"job_id": "JOB_A05", "title": "退役军人创业项目评估师", "policy_relations": ["POLICY_A06"]}
    ];
    
    console.log('加载的岗位数据:', jobsData);
    
    // 提取涉及到的政策ID
    const involvedPolicyIds = [];
    if (relevantPolicies && relevantPolicies.length > 0) {
        relevantPolicies.forEach(policy => {
            if (policy.policy_id) {
                involvedPolicyIds.push(policy.policy_id);
            }
        });
    }
    
    // 额外处理：从positiveContent中提取可能的政策ID
    if (typeof positiveContent === 'string' && positiveContent.trim() !== '') {
        // 尝试从文本中匹配政策ID格式，如POLICY_A01
        const policyIdMatches = positiveContent.match(/POLICY_[A-Z0-9]+/g);
        if (policyIdMatches) {
            policyIdMatches.forEach(policyId => {
                if (!involvedPolicyIds.includes(policyId)) {
                    involvedPolicyIds.push(policyId);
                }
            });
        }
    }
    
    console.log('涉及到的政策ID:', involvedPolicyIds);
    
    // 根据政策和用户意图找到相关岗位
    const relatedJobs = [];
    if (involvedPolicyIds.length > 0) {
        // 从数据中提取用户意图信息
        let userIntent = '';
        let hasVeteran = false;
        let hasEcommerce = false;
        let hasEntrepreneurship = false;
        let hasIncubator = false;
        
        // 检查相关政策
        relevantPolicies.forEach(policy => {
            if (policy.policy_id === "POLICY_A06") {
                hasVeteran = true;
            }
            if (policy.policy_id === "POLICY_A04") {
                hasIncubator = true;
            }
        });
        
        // 检查思考过程中的信息
        if (thinkingProcess && thinkingProcess.length > 0) {
            thinkingProcess.forEach(step => {
                if (step.content) {
                    userIntent += step.content;
                }
                if (step.substeps && step.substeps.length > 0) {
                    step.substeps.forEach(substep => {
                        if (substep.content) {
                            userIntent += substep.content;
                        }
                    });
                }
            });
        }
        
        // 检查用户意图中的关键词和否定词
        hasEcommerce = userIntent.includes("电商") && !userIntent.includes("没有电商") && !userIntent.includes("未选择电商") && !userIntent.includes("不做电商");
        hasEntrepreneurship = userIntent.includes("创业") && !userIntent.includes("没有创业") && !userIntent.includes("未选择创业") && !userIntent.includes("不创业");
        hasIncubator = hasIncubator || (userIntent.includes("孵化基地") && !userIntent.includes("没有入驻") && !userIntent.includes("未入驻"));
        hasVeteran = hasVeteran || userIntent.includes("退役军人");
        
        console.log('用户意图分析:', { hasVeteran, hasEcommerce, hasEntrepreneurship, hasIncubator });
        
        jobsData.forEach(job => {
            // 检查岗位是否与政策相关
            const isPolicyRelated = job.policy_relations && job.policy_relations.some(policyId => involvedPolicyIds.includes(policyId));
            
            // 检查岗位是否与用户意图相关
            let isIntentRelated = true;
            
            // 特殊处理：电商创业辅导专员（JOB_A03）
            if (job.job_id === "JOB_A03") {
                // 只有当用户明确提到电商创业时才推荐，单纯提到创业不足以推荐
                isIntentRelated = hasEcommerce;
            }
            
            // 特殊处理：退役军人创业项目评估师（JOB_A05）
            if (job.job_id === "JOB_A05") {
                // 只有当用户是退役军人时才推荐
                isIntentRelated = hasVeteran;
            }
            
            // 特殊处理：创业孵化基地管理员（JOB_A01）
            if (job.job_id === "JOB_A01") {
                // 只有当用户提到创业或孵化基地时才推荐
                isIntentRelated = hasEntrepreneurship || hasIncubator;
            }
            
            // 只有同时满足政策相关和意图相关的岗位才推荐
            if (isPolicyRelated && isIntentRelated) {
                relatedJobs.push(job);
            }
        });
    }
    
    console.log('相关岗位:', relatedJobs);
    
    // 根据符合条件的政策生成建议
    if (typeof positiveContent === 'string' && positiveContent.trim() !== '' && positiveContent.trim() !== '无') {
        suggestions.push('符合政策条件，建议及时准备材料申请。');
        suggestions.push('政策详情：' + positiveContent);
        suggestions.push('建议联系当地人力资源和社会保障部门咨询政策申请流程。');
        if (jobsData.length > 0) {
            // 优先显示相关岗位，如果没有则显示所有岗位
            const displayJobs = relatedJobs.length > 0 ? relatedJobs : jobsData;
            const jobInfo = displayJobs.map(job => `${job.title}（${job.job_id}）`).join('、');
            suggestions.push(`可咨询以下岗位获取政策支持：${jobInfo}`);
        }
    }
    
    // 如果没有符合条件的政策，提供一般政策咨询建议
    if (typeof negativeContent === 'string' && negativeContent.trim() !== '' && negativeContent.trim() !== '无') {
        suggestions.push('不符合政策条件的原因：' + negativeContent);
        suggestions.push('建议关注相关政策动态，了解申请条件变化。');
        suggestions.push('建议联系当地人力资源和社会保障部门咨询相关政策。');
    }
    
    // 如果没有政策相关信息，提供一般政策咨询建议
    if ((!positiveContent || positiveContent.trim() === '' || positiveContent.trim() === '无') && (!negativeContent || negativeContent.trim() === '' || negativeContent.trim() === '无')) {
        suggestions.push('建议联系当地人力资源和社会保障部门咨询相关政策。');
        if (jobsData.length > 0) {
            // 优先显示相关岗位，如果没有则显示所有岗位
            const displayJobs = relatedJobs.length > 0 ? relatedJobs : jobsData;
            const jobInfo = displayJobs.map(job => `${job.title}（${job.job_id}）`).join('、');
            suggestions.push(`可咨询以下岗位获取更多信息：${jobInfo}`);
        }
    }
    
    // 如果有建议，组合成主动建议内容
    if (suggestions.length > 0) {
        dynamicSuggestions = suggestions.join('\n\n');
    }
    
    // 优先使用后端返回的简历优化建议，确保基于推荐岗位的具体方案能够显示
    const finalSuggestionsContent = suggestionsContent || dynamicSuggestions;
    
    // 构建分析结果HTML（不包含思考过程，因为我们要保留原有的思考过程）
    let analysisHtml = `
        <div class="analysis-result">
            ${answerContent && typeof answerContent === 'string' && answerContent.trim() !== '' ? `
            <div class="card-section">
                <div class="answer-card">
                    <div class="answer-content">${answerContent}</div>
                </div>
            </div>
            ` : ''}
            
            ${recommendedJobs.length > 0 ? `
            <div class="card-section">
                <h3>💼 推荐岗位</h3>
                <div class="jobs-card">
                    ${recommendedJobs.map((job, index) => `
                    <div class="job-item">
                        <div class="job-title">${job.title} <span class="job-id">(${job.job_id || 'ID未提供'})</span> <span class="job-priority">优先级: ${index + 1}</span></div>
                        <div class="job-reasons">
                            <strong>推荐理由:</strong> ${job.reasons && job.reasons.positive ? job.reasons.positive : '无具体推荐理由'}
                        </div>
                        <div class="job-features">
                            <strong>特点:</strong> ${job.features || '无具体特点'}
                        </div>
                    </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}
            
            ${recommendedCourses.length > 0 ? `
            <div class="card-section">
                <h3>📚 推荐课程</h3>
                <div class="courses-card">
                    ${recommendedCourses.map((course, index) => `
                    <div class="course-item">
                        <div class="course-title">${course.title} <span class="course-id">(${course.course_id || 'ID未提供'})</span> <span class="course-priority">优先级: ${index + 1}</span></div>
                        <div class="course-reasons">
                            <strong>推荐理由:</strong> ${course.reasons && course.reasons.positive ? course.reasons.positive : '无具体推荐理由'}
                        </div>
                        <div class="course-features">
                            <strong>成长路径:</strong> ${course.growth_path || '无具体成长路径'}
                        </div>
                    </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}
            
            ${typeof positiveContent === 'string' && positiveContent.trim() !== '' && positiveContent.trim() !== '无' ? `
            <div class="card-section">
                <h3>✅ 符合条件的政策</h3>
                <div class="policy-card">
                    <div class="policy-reasons">
                        <div class="reason positive">
                            <div class="reason-content">
                                <div class="reason-text">${positiveContent}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            ` : ''}
            
            ${typeof negativeContent === 'string' && negativeContent.trim() !== '' && negativeContent.trim() !== '无' ? `
            <div class="card-section">
                <h3>❌ 不符合条件的政策</h3>
                <div class="policy-card">
                    <div class="policy-reasons">
                        <div class="reason negative">
                            <div class="reason-content">
                                <div class="reason-text">${negativeContent}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            ` : ''}
            
            ${typeof finalSuggestionsContent === 'string' && finalSuggestionsContent.trim() !== '' && finalSuggestionsContent.trim() !== '无' ? `
            <div class="card-section">
                <h3>💡 主动建议</h3>
                <div class="suggestions-card">
                    <div class="suggestion-item">${finalSuggestionsContent}</div>
                </div>
            </div>
            ` : ''}
        </div>
    `;
    
    console.log('生成的分析结果HTML:', analysisHtml);
    
    // 检查容器中是否已经有思考过程
    const existingThinkingContainer = container.querySelector('.thinking-container');
    
    if (existingThinkingContainer) {
        // 如果已经有思考过程，只添加分析结果部分
        // 找到message-content元素
        const messageContent = container.querySelector('.message-content');
        if (messageContent) {
            // 创建分析结果容器
            const analysisContainer = document.createElement('div');
            analysisContainer.innerHTML = analysisHtml;
            // 将分析结果添加到message-content中，在思考过程容器之后
            messageContent.appendChild(analysisContainer);
        }
    } else {
        // 如果没有思考过程，使用完整的HTML
        // 构建思考过程HTML
        let thinkingProcessHtml = '';
        if (thinkingProcess.length > 0) {
            thinkingProcessHtml = `
            <div class="thinking-container finished">
                <div class="thinking-header" onclick="toggleThinking(this)">
                    <span class="thinking-title">思考过程</span>
                    <span class="thinking-toggle-icon"></span>
                </div>
                <div class="thinking-content has-content">
            `;
            
            // 递归函数处理步骤和子步骤
            function renderSteps(steps, level = 0) {
                let html = '';
                const indentClass = level === 0 ? 'thinking-step' : level === 1 ? 'thinking-substep' : 'thinking-subsubstep';
                
                steps.forEach(step => {
                    if (level === 0) {
                        // 主步骤 - 使用标题和内容分离的结构
                        html += `<div class="${indentClass}">
                            <div class="thinking-step-title">${step.step}</div>
                            <div class="thinking-step-content">${step.content}</div>
                        </div>`;
                    } else {
                        // 子步骤和子子步骤
                        html += `<div class="${indentClass}">
                            <strong>${step.step}:</strong> ${step.content}
                        </div>`;
                    }
                    
                    // 递归处理子步骤
                    if (step.substeps && step.substeps.length > 0) {
                        html += renderSteps(step.substeps, level + 1);
                    }
                });
                
                return html;
            }
            
            // 使用递归函数渲染所有步骤
            thinkingProcessHtml += renderSteps(thinkingProcess);
            
            thinkingProcessHtml += `
                </div>
            </div>
            `;
        } else if (intentData) {
            // 兼容意图数据格式
            thinkingProcessHtml = `
            <div class="thinking-container finished">
                <div class="thinking-header" onclick="toggleThinking(this)">
                    <span class="thinking-title">思考过程</span>
                    <span class="thinking-toggle-icon"></span>
                </div>
                <div class="thinking-content has-content">
                    <div class="thinking-step"><strong>意图与实体识别:</strong> 核心意图 "${intentData.intent}"，提取实体: ${intentData.entities && intentData.entities.length > 0 ? intentData.entities.map(entity => `${entity.value}(${entity.type})`).join(', ') : '无'}${!intentData.entities || !intentData.entities.some(e => e.value && e.value.includes('就业')) ? ', 带动就业（未提及）' : ''}</div>
                    ${relevantPolicies.length > 0 ? `
                    <div class="thinking-step"><strong>精准检索与推理:</strong></div>
                    <div class="thinking-substeps">
                        ${relevantPolicies.map(policy => {
                            if (policy.policy_id === 'POLICY_A03') {
                                return `<div class="thinking-substep"><strong>检索${policy.policy_id}:</strong> 判断"创办小微企业+正常经营1年+带动3人以上就业"可申领2万一次性补贴，用户未提"带动就业"，需指出缺失条件</div>`;
                            } else if (policy.policy_id === 'POLICY_A01') {
                                return `<div class="thinking-substep"><strong>检索${policy.policy_id}:</strong> 确认其"返乡农民工"身份符合贷款申请条件，说明额度（≤50万）、期限（≤3年）及贴息规则</div>`;
                            } else {
                                return `<div class="thinking-substep"><strong>检索${policy.policy_id}:</strong> 分析${policy.title || '政策'}的适用条件</div>`;
                            }
                        }).join('')}
                    </div>
                    ` : ''}
                </div>
            </div>
            `;
        }
        
        // 构建完整的HTML
        let fullHtml = `
            <div class="message-avatar">🤖</div>
            <div class="message-content">
                ${thinkingProcessHtml}
                ${analysisHtml}
            </div>
        `;
        
        container.innerHTML = fullHtml;
    }
    
    scrollToBottom();
}

// 获取优先级颜色
function getPriorityColor(priority) {
    const colors = {
        5: '#10b981', // 绿色
        4: '#3b82f6', // 蓝色
        3: '#f59e0b', // 橙色
        2: '#ef4444', // 红色
        1: '#6b7280'  // 灰色
    };
    return colors[priority] || '#6b7280';
}

// 切换思考过程显示
function toggleThinking(header) {
    const container = header.closest('.thinking-container');
    container.classList.toggle('active');
    
    const icon = header.querySelector('.thinking-toggle-icon');
    if (container.classList.contains('active')) {
        icon.style.transform = 'rotate(180deg)';
    } else {
        icon.style.transform = 'rotate(0)';
    }
}

// 滚动到底部
function scrollToBottom() {
    const chatContainer = document.getElementById('chat-container');
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// 隐藏评估结果
function hideEvaluation() {
    const evaluationToast = document.getElementById('evaluation-toast');
    if (evaluationToast) {
        evaluationToast.style.display = 'none';
    }
}

// 加载用户画像
async function loadUserProfile() {
    // 这里可以实现加载用户画像的逻辑
    // 暂时留空
}

// 保存用户画像
async function saveUserProfile() {
    // 这里可以实现保存用户画像的逻辑
    // 暂时留空
}

// 关闭用户画像模态框
function closeProfileModal() {
    const modal = document.getElementById('profile-modal');
    modal.style.display = 'none';
}
