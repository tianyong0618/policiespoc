import json
import os
import time
import uuid
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - HistoryManager - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HistoryManager:
    def __init__(self, storage_file='../data/data_files/chat_history.json'):
        self.storage_file = os.path.join(os.path.dirname(__file__), storage_file)
        self.sessions = self._load_history()

    def _load_history(self):
        """加载历史记录"""
        if not os.path.exists(self.storage_file):
            return {}
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载历史记录失败: {e}")
            return {}

    def _save_history(self):
        """保存历史记录"""
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存历史记录失败: {e}")

    def create_session(self, title="新对话"):
        """创建新会话"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "id": session_id,
            "title": title,
            "created_at": time.time(),
            "updated_at": time.time(),
            "messages": []
        }
        self._save_history()
        return session_id

    def get_session(self, session_id):
        """获取会话详情"""
        return self.sessions.get(session_id)

    def get_all_sessions(self):
        """获取所有会话列表（按时间倒序）"""
        sessions_list = list(self.sessions.values())
        # 按更新时间倒序排列
        sessions_list.sort(key=lambda x: x.get('updated_at', 0), reverse=True)
        # 只返回摘要信息
        return [{
            "id": s["id"],
            "title": s["title"],
            "created_at": s["created_at"],
            "updated_at": s.get("updated_at", s["created_at"])
        } for s in sessions_list]

    def add_message(self, session_id, role, content):
        """添加消息"""
        if session_id not in self.sessions:
            logger.warning(f"会话 {session_id} 不存在，自动创建")
            self.create_session()
            # 如果是新建的，用第一条消息内容作为标题
            if role == 'user':
                self.sessions[session_id]["title"] = content[:20] + "..." if len(content) > 20 else content

        session = self.sessions[session_id]
        session["messages"].append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })
        session["updated_at"] = time.time()
        
        # 如果是第一条用户消息，且标题仍为默认值，更新标题
        if role == 'user' and len(session["messages"]) == 1:
             session["title"] = content[:20] + "..." if len(content) > 20 else content
        elif role == 'user' and session["title"] == "新对话":
             session["title"] = content[:20] + "..." if len(content) > 20 else content

        self._save_history()

    def delete_session(self, session_id):
        """删除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self._save_history()
            return True
        return False
