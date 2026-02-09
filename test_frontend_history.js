#!/usr/bin/env node
/**
 * 测试前端历史记录加载功能
 * 模拟后端服务未启动时的情况
 */

// 使用Node.js 18+内置的fetch API

// 模拟前端的loadHistoryList函数
async function testLoadHistoryList() {
    console.log('测试加载历史记录...');
    
    try {
        const response = await fetch('http://localhost:8000/api/history');
        if (!response.ok) {
            console.log('❌ API请求失败，状态码:', response.status);
            // 模拟前端错误处理
            console.log('✅ 前端会显示: "暂无历史记录"');
            return;
        }
        
        const data = await response.json();
        console.log('✅ API请求成功，返回数据:');
        console.log(JSON.stringify(data, null, 2));
        
        if (data.sessions && data.sessions.length > 0) {
            console.log('✅ 前端会显示真实历史记录');
        } else {
            console.log('✅ 前端会显示: "暂无历史记录"');
        }
        
    } catch (error) {
        console.log('❌ API请求出错:', error.message);
        // 模拟前端错误处理
        console.log('✅ 前端会显示: "暂无历史记录"');
    }
}

// 运行测试
testLoadHistoryList();
