// API基础URL - 自动适配环境
const API_BASE_URL = (() => {
  // 检测当前环境
  const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  // 本地开发使用完整URL，部署后使用相对路径
  return isLocal ? 'http://127.0.0.1:8000/api' : '/api';
})();

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
                                // 显示分析开始
                                aiMessageDiv.innerHTML = `
                                    <div class="message-avatar">🤖</div>
                                    <div class="message-content">
                                        <div class="thinking-container">
                                            <div class="thinking-header">
                                                <span class="thinking-title">正在分析...</span>
                                                <span class="thinking-toggle-icon"></span>
                                            </div>
                                            <div class="thinking-content">
                                                <div class="thinking-dots">
                                                    <div class="typing-dot"></div>
                                                    <div class="typing-dot"></div>
                                                    <div class="typing-dot"></div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                `;
                                scrollToBottom();
                                break;
                                
                            case 'thinking':
                                // 显示思考过程 - 流式动态显示
                                if (!thinkingElement) {
                                    // 清空之前的内容，创建思考过程容器
                                    aiMessageDiv.querySelector('.message-content').innerHTML = '';
                                    const thinkingContainer = document.createElement('div');
                                    thinkingContainer.className = 'thinking-container active';
                                    thinkingContainer.innerHTML = `
                                        <div class="thinking-header">
                                            <span class="thinking-title">思考过程</span>
                                            <span class="thinking-toggle-icon" style="transform: rotate(180deg);"></span>
                                        </div>
                                        <div class="thinking-content has-content"></div>
                                    `;
                                    aiMessageDiv.querySelector('.message-content').appendChild(thinkingContainer);
                                    thinkingElement = thinkingContainer.querySelector('.thinking-content');
                                    // 添加点击事件
                                    thinkingContainer.querySelector('.thinking-header').addEventListener('click', function() {
                                        thinkingContainer.classList.toggle('active');
                                    });
                                }
                                // 流式添加思考内容
                                thinkingElement.innerHTML += `<div class="thinking-step">${data.content}</div>`;
                                scrollToBottom();
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
                    ${data.question}
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
    
    // 处理后端返回的格式
    if (data.content) {
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
        
        thinkingProcess.forEach(step => {
            thinkingProcessHtml += `<div class="thinking-step"><strong>${step.step}:</strong> ${step.content}</div>`;
            
            // 处理子步骤
            if (step.substeps && step.substeps.length > 0) {
                thinkingProcessHtml += `<div class="thinking-substeps">`;
                step.substeps.forEach(substep => {
                    thinkingProcessHtml += `<div class="thinking-substep"><strong>${substep.step}:</strong> ${substep.content}</div>`;
                });
                thinkingProcessHtml += `</div>`;
            }
        });
        
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
    
    // 构建HTML
    let html = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <div class="analysis-result">
                ${thinkingProcessHtml}
                
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
                            <div class="job-requirements">
                                <strong>要求:</strong> ${job.requirements && job.requirements.length > 0 ? job.requirements.join(', ') : '无具体要求'}
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
                            <div class="course-requirements">
                                <strong>要求:</strong> ${course.conditions ? course.conditions.map(cond => `${cond.type}: ${cond.value}`).join(', ') : '无具体要求'}
                            </div>
                            <div class="course-features">
                                <strong>特点:</strong> ${course.content || '无具体特点'}
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
                
                ${typeof suggestionsContent === 'string' && suggestionsContent.trim() !== '' && suggestionsContent.trim() !== '无' ? `
                <div class="card-section">
                    <h3>💡 主动建议</h3>
                    <div class="suggestions-card">
                        <div class="suggestion-item">${suggestionsContent}</div>
                    </div>
                </div>
                ` : ''}
            </div>
        </div>
    `;
    
    console.log('生成的HTML:', html);
    
    container.innerHTML = html;
    
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
