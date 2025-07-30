import unittest
import json
import time
from unittest.mock import patch, MagicMock
import sys
import os

# 添加主模块到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, conversation_mapper, ConversationMapper, extract_webui_chat_id, update_conversation_mapping


class TestConversationMapping(unittest.TestCase):
    """测试会话映射功能"""
    
    def setUp(self):
        """设置测试环境"""
        self.app = app.test_client()
        self.app.testing = True
        # 使用测试专用的存储文件
        self.test_storage = "data/test_conversation_mappings.json"
        conversation_mapper.storage_file = self.test_storage
        # 清空映射器状态
        conversation_mapper._mapping.clear()
    
    def tearDown(self):
        """清理测试环境"""
        conversation_mapper._mapping.clear()
        # 清理测试文件
        if os.path.exists(self.test_storage):
            os.remove(self.test_storage)


class TestConversationMapper(TestConversationMapping):
    """测试 ConversationMapper 类"""
    
    def test_mapper_initialization(self):
        """测试映射器初始化"""
        mapper = ConversationMapper()
        self.assertEqual(mapper.get_mapping_count(), 0)
        self.assertIsInstance(mapper._mapping, dict)
    
    def test_set_and_get_mapping(self):
        """测试设置和获取映射"""
        webui_chat_id = "test-webui-chat-123"
        dify_conversation_id = "test-dify-conv-456"
        
        # 设置映射
        conversation_mapper.set_mapping(webui_chat_id, dify_conversation_id)
        
        # 验证映射
        self.assertEqual(
            conversation_mapper.get_dify_conversation_id(webui_chat_id),
            dify_conversation_id
        )
        self.assertTrue(conversation_mapper.has_mapping(webui_chat_id))
        self.assertEqual(conversation_mapper.get_mapping_count(), 1)
    
    def test_nonexistent_mapping(self):
        """测试不存在的映射"""
        result = conversation_mapper.get_dify_conversation_id("nonexistent")
        self.assertIsNone(result)
        self.assertFalse(conversation_mapper.has_mapping("nonexistent"))
    
    def test_remove_mapping(self):
        """测试删除映射"""
        webui_chat_id = "test-webui-chat-123"
        dify_conversation_id = "test-dify-conv-456"
        
        # 设置映射
        conversation_mapper.set_mapping(webui_chat_id, dify_conversation_id)
        self.assertEqual(conversation_mapper.get_mapping_count(), 1)
        
        # 删除映射
        result = conversation_mapper.remove_mapping(webui_chat_id)
        self.assertTrue(result)
        self.assertEqual(conversation_mapper.get_mapping_count(), 0)
        self.assertFalse(conversation_mapper.has_mapping(webui_chat_id))
        
        # 删除不存在的映射
        result = conversation_mapper.remove_mapping("nonexistent")
        self.assertFalse(result)
    
    def test_thread_safety(self):
        """测试线程安全性"""
        import threading
        
        webui_chat_id = "thread-test-123"
        dify_conversation_id = "thread-dify-456"
        
        def set_mapping():
            conversation_mapper.set_mapping(webui_chat_id, dify_conversation_id)
        
        def get_mapping():
            return conversation_mapper.get_dify_conversation_id(webui_chat_id)
        
        # 并发执行
        threads = []
        for i in range(10):
            t = threading.Thread(target=set_mapping)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # 验证结果
        self.assertEqual(
            conversation_mapper.get_dify_conversation_id(webui_chat_id),
            dify_conversation_id
        )


class TestExtractWebUIChatId(TestConversationMapping):
    """测试提取 WebUI chat_id 功能"""
    
    def test_extract_from_header(self):
        """测试从 HTTP Header 提取 chat_id"""
        test_chat_id = "header-test-123"
        
        with app.test_request_context(headers={'X-OpenWebUI-Chat-Id': test_chat_id}):
            result = extract_webui_chat_id()
            self.assertEqual(result, test_chat_id)
    
    def test_extract_from_metadata(self):
        """测试从 metadata 提取 chat_id"""
        test_chat_id = "metadata-test-456"
        test_data = {'metadata': {'chat_id': test_chat_id}}
        
        with app.test_request_context(json=test_data, content_type='application/json'):
            result = extract_webui_chat_id()
            self.assertEqual(result, test_chat_id)
    
    def test_extract_no_chat_id(self):
        """测试没有 chat_id 的情况"""
        with app.test_request_context():
            result = extract_webui_chat_id()
            self.assertIsNone(result)
    
    def test_extract_header_priority(self):
        """测试 Header 优先于 metadata"""
        header_chat_id = "header-priority-123"
        metadata_chat_id = "metadata-secondary-456"
        test_data = {'metadata': {'chat_id': metadata_chat_id}}
        
        with app.test_request_context(
            json=test_data,
            headers={'X-OpenWebUI-Chat-Id': header_chat_id},
            content_type='application/json'
        ):
            result = extract_webui_chat_id()
            self.assertEqual(result, header_chat_id)


class TestUpdateConversationMapping(TestConversationMapping):
    """测试更新会话映射功能"""
    
    def test_update_new_mapping(self):
        """测试创建新的映射"""
        webui_chat_id = "update-test-123"
        dify_response = {
            "conversation_id": "dify-conv-789",
            "message_id": "msg-123"
        }
        
        # 执行更新
        update_conversation_mapping(webui_chat_id, dify_response)
        
        # 验证映射已创建
        self.assertTrue(conversation_mapper.has_mapping(webui_chat_id))
        self.assertEqual(
            conversation_mapper.get_dify_conversation_id(webui_chat_id),
            "dify-conv-789"
        )
    
    def test_update_existing_mapping(self):
        """测试更新已存在的映射"""
        webui_chat_id = "existing-test-123"
        old_dify_id = "old-dify-conv-123"
        new_dify_id = "new-dify-conv-456"
        
        # 先设置映射
        conversation_mapper.set_mapping(webui_chat_id, old_dify_id)
        
        # 尝试更新（应该不会改变）
        dify_response = {"conversation_id": new_dify_id}
        update_conversation_mapping(webui_chat_id, dify_response)
        
        # 验证映射没有改变
        self.assertEqual(
            conversation_mapper.get_dify_conversation_id(webui_chat_id),
            old_dify_id
        )
    
    def test_update_no_conversation_id(self):
        """测试响应中没有 conversation_id 的情况"""
        webui_chat_id = "no-conv-id-test"
        dify_response = {"message_id": "msg-123"}
        
        # 执行更新
        update_conversation_mapping(webui_chat_id, dify_response)
        
        # 验证没有创建映射
        self.assertFalse(conversation_mapper.has_mapping(webui_chat_id))
    
    def test_update_no_webui_chat_id(self):
        """测试没有 webui_chat_id 的情况"""
        dify_response = {"conversation_id": "dify-conv-123"}
        
        # 执行更新（不应该抛出异常）
        update_conversation_mapping(None, dify_response)
        update_conversation_mapping("", dify_response)
        
        # 验证没有创建任何映射
        self.assertEqual(conversation_mapper.get_mapping_count(), 0)


class TestIntegration(TestConversationMapping):
    """集成测试"""
    
    @patch.dict(os.environ, {
        'MODEL_CONFIG': '{"test-model": "test-api-key"}',
        'DIFY_API_BASE': 'https://test-dify-api.com/v1'
    })
    def test_mappings_endpoint(self):
        """测试映射状态查询端点"""
        # 添加一些映射
        conversation_mapper.set_mapping("chat-1", "conv-1")
        conversation_mapper.set_mapping("chat-2", "conv-2")
        
        # 调用端点
        response = self.app.get('/v1/conversation/mappings')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['mapping_count'], 2)
        self.assertIn('timestamp', data)
    
    @patch('main.get_http_client')
    @patch('main.MODEL_TO_API_KEY', {"test-model": "test-api-key"})
    def test_chat_completions_with_mapping(self, mock_get_client):
        """测试带有映射的聊天完成请求"""
        # 模拟数据
        webui_chat_id = "integration-test-123"
        dify_conversation_id = "dify-integration-456"
        
        # 模拟 HTTP 客户端
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "conversation_id": dify_conversation_id,
            "message_id": "msg-123",
            "answer": "Test response"
        }
        mock_client.post.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        # 发送请求（带有 chat_id header）
        response = self.app.post('/v1/chat/completions', 
            json={
                "model": "test-model",
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": False
            },
            headers={
                'Content-Type': 'application/json',
                'X-OpenWebUI-Chat-Id': webui_chat_id
            }
        )
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        
        # 验证映射已创建
        self.assertTrue(conversation_mapper.has_mapping(webui_chat_id))
        self.assertEqual(
            conversation_mapper.get_dify_conversation_id(webui_chat_id),
            dify_conversation_id
        )


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)