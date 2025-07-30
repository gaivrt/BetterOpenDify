import json
import logging
from flask import Flask, request, Response, stream_with_context
import httpx
import time
from dotenv import load_dotenv
import os
import ast
from threading import Lock
from typing import Dict, Optional

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 设置 httpx 的日志级别
logging.getLogger("httpx").setLevel(logging.DEBUG)

# 加载环境变量
load_dotenv()

class ConversationMapper:
    """管理 Open WebUI chat_id 到 Dify conversation_id 的映射关系"""
    
    def __init__(self, storage_file="data/conversation_mappings.json"):
        # 确保数据目录存在
        os.makedirs(os.path.dirname(storage_file), exist_ok=True)
        self.storage_file = storage_file
        self._mapping: Dict[str, dict] = {}  # 改为dict存储更多信息
        self._lock = Lock()
        self._load_mappings()
        logger.info("✅ ConversationMapper initialized")
    
    def _load_mappings(self) -> None:
        """从文件加载映射关系"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._mapping = data
                    logger.info(f"📂 Loaded {len(self._mapping)} conversation mappings from {self.storage_file}")
            else:
                logger.info(f"📂 No existing mappings file found, starting fresh")
        except Exception as e:
            logger.error(f"❌ Failed to load mappings from {self.storage_file}: {e}")
            self._mapping = {}
    
    def _save_mappings(self) -> None:
        """保存映射关系到文件"""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self._mapping, f, ensure_ascii=False, indent=2)
            logger.debug(f"💾 Saved {len(self._mapping)} mappings to {self.storage_file}")
        except Exception as e:
            logger.error(f"❌ Failed to save mappings to {self.storage_file}: {e}")
    
    def get_dify_conversation_id(self, webui_chat_id: str) -> Optional[str]:
        """根据 Open WebUI chat_id 获取对应的 Dify conversation_id"""
        with self._lock:
            mapping_info = self._mapping.get(webui_chat_id)
            return mapping_info.get('dify_conversation_id') if mapping_info else None
    
    def set_mapping(self, webui_chat_id: str, dify_conversation_id: str) -> None:
        """设置映射关系"""
        with self._lock:
            self._mapping[webui_chat_id] = {
                'dify_conversation_id': dify_conversation_id,
                'created_at': int(time.time()),
                'last_used': int(time.time())
            }
            self._save_mappings()  # 立即持久化
            logger.info(f"🔗 Mapped WebUI chat_id {webui_chat_id[:8]}... to Dify conversation_id {dify_conversation_id[:8]}...")
    
    def has_mapping(self, webui_chat_id: str) -> bool:
        """检查是否存在映射关系"""
        with self._lock:
            return webui_chat_id in self._mapping
    
    def remove_mapping(self, webui_chat_id: str) -> bool:
        """删除映射关系"""
        with self._lock:
            if webui_chat_id in self._mapping:
                del self._mapping[webui_chat_id]
                self._save_mappings()  # 立即持久化
                logger.info(f"🗑️  Removed mapping for WebUI chat_id {webui_chat_id[:8]}...")
                return True
            return False
    
    def get_mapping_count(self) -> int:
        """获取当前映射数量"""
        with self._lock:
            return len(self._mapping)
    
    def update_last_used(self, webui_chat_id: str) -> None:
        """更新映射的最后使用时间"""
        with self._lock:
            if webui_chat_id in self._mapping:
                self._mapping[webui_chat_id]['last_used'] = int(time.time())
                self._save_mappings()
    
    def cleanup_old_mappings(self, max_age_days: int = 30) -> int:
        """清理超过指定天数的映射"""
        cutoff_time = int(time.time()) - (max_age_days * 24 * 60 * 60)
        removed_count = 0
        
        with self._lock:
            keys_to_remove = []
            for chat_id, mapping_info in self._mapping.items():
                if mapping_info.get('last_used', 0) < cutoff_time:
                    keys_to_remove.append(chat_id)
            
            for key in keys_to_remove:
                del self._mapping[key]
                removed_count += 1
            
            if removed_count > 0:
                self._save_mappings()
                logger.info(f"🧹 Cleaned up {removed_count} old mappings (older than {max_age_days} days)")
        
        return removed_count
    
    def get_mapping_stats(self) -> dict:
        """获取映射统计信息"""
        with self._lock:
            if not self._mapping:
                return {"total": 0, "oldest": None, "newest": None}
            
            created_times = [info.get('created_at', 0) for info in self._mapping.values()]
            return {
                "total": len(self._mapping),
                "oldest": min(created_times) if created_times else None,
                "newest": max(created_times) if created_times else None
            }

# 全局会话映射器实例
conversation_mapper = ConversationMapper()

def parse_model_config():
    """
    从环境变量解析模型配置
    返回一个字典 {model_name: api_key}
    """
    try:
        config_str = os.getenv('MODEL_CONFIG', '{}')
        if not config_str.strip():
            logger.warning("MODEL_CONFIG is empty, no models will be available")
            return {}
            
        # 尝试作为Python字典解析
        try:
            result = ast.literal_eval(config_str)
            if not isinstance(result, dict):
                logger.error("MODEL_CONFIG must be a dictionary")
                return {}
            return result
        except (SyntaxError, ValueError) as e:
            logger.error(f"Failed to parse MODEL_CONFIG as Python dict: {e}")
            try:
                # 尝试作为JSON解析
                result = json.loads(config_str)
                if not isinstance(result, dict):
                    logger.error("MODEL_CONFIG must be a dictionary")
                    return {}
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse MODEL_CONFIG as JSON: {e}")
                return {}
    except Exception as e:
        logger.error(f"Error parsing MODEL_CONFIG: {e}")
        return {}

def validate_startup_config():
    """验证启动配置"""
    issues = []
    
    # 检查必需的环境变量
    dify_api_base = os.getenv("DIFY_API_BASE", "")
    if not dify_api_base.strip():
        issues.append("DIFY_API_BASE is not set or empty")
    elif not (dify_api_base.startswith("http://") or dify_api_base.startswith("https://")):
        issues.append(f"DIFY_API_BASE must be a valid URL, got: {dify_api_base}")
    
    # 检查模型配置
    if not MODEL_TO_API_KEY:
        issues.append("No valid models configured in MODEL_CONFIG")
    else:
        for model_name, api_key in MODEL_TO_API_KEY.items():
            if not api_key or not api_key.strip():
                issues.append(f"Empty API key for model: {model_name}")
            elif not isinstance(api_key, str):
                issues.append(f"API key must be string for model: {model_name}")
    
    # 报告问题
    if issues:
        logger.error("Configuration validation failed:")
        for issue in issues:
            logger.error(f"  - {issue}")
        logger.error("Please check your .env file and fix these issues")
        return False
    
    logger.info("✅ Configuration validation passed")
    logger.info(f"✅ Loaded {len(MODEL_TO_API_KEY)} model(s): {', '.join(MODEL_TO_API_KEY.keys())}")
    logger.info(f"✅ Dify API base: {dify_api_base}")
    return True

# 从环境变量获取配置
MODEL_TO_API_KEY = parse_model_config()

# 根据MODEL_TO_API_KEY自动生成模型信息
AVAILABLE_MODELS = [
    {
        "id": model_id,
        "object": "model",
        "created": int(time.time()),
        "owned_by": "dify"
    }
    for model_id, api_key in MODEL_TO_API_KEY.items()
    if api_key is not None  # 只包含配置了API Key的模型
]

app = Flask(__name__)

# 从环境变量获取API基础URL
DIFY_API_BASE = os.getenv("DIFY_API_BASE", "https://mify-be.pt.xiaomi.com/api/v1")

# 全局HTTP客户端配置
HTTP_CLIENT_CONFIG = {
    "timeout": 30.0,
    "limits": httpx.Limits(max_keepalive_connections=20, max_connections=100),
    "follow_redirects": True
}

# 全局HTTP客户端实例（延迟初始化）
_http_client = None

def get_http_client():
    """获取或创建全局HTTP客户端"""
    global _http_client
    if _http_client is None:
        _http_client = httpx.Client(**HTTP_CLIENT_CONFIG)
        logger.info("✅ HTTP client initialized with connection pooling")
    return _http_client

def cleanup_http_client():
    """清理HTTP客户端资源"""
    global _http_client
    if _http_client is not None:
        _http_client.close()
        _http_client = None
        logger.info("✅ HTTP client resources cleaned up")

def get_api_key(model_name):
    """根据模型名称获取对应的API密钥"""
    api_key = MODEL_TO_API_KEY.get(model_name)
    if not api_key:
        logger.warning(f"No API key found for model: {model_name}")
    return api_key

def extract_webui_chat_id() -> Optional[str]:
    """从请求中提取 Open WebUI 的 chat_id"""
    # 调试：打印所有请求头
    logger.debug(f"🔍 All headers: {dict(request.headers)}")
    
    # 调试：逐个打印每个头部的名称和值
    logger.debug("🔍 Raw headers inspection:")
    for header_name, header_value in request.headers:
        logger.debug(f"🔍   '{header_name}' = '{header_value}'")
        # 检查是否包含chat-id相关字符串
        if 'chat' in header_name.lower():
            logger.debug(f"🔍   ^^^ This header contains 'chat'!")
    
    # 方法1: 从 HTTP Header 提取 (支持多种大小写形式)
    possible_headers = ['X-OpenWebUI-Chat-Id', 'x-openwebui-chat-id', 'X-Openwebui-Chat-Id']
    chat_id = None
    
    for header_name in possible_headers:
        chat_id = request.headers.get(header_name)
        if chat_id:
            logger.debug(f"🔍 Found chat_id in header '{header_name}': {chat_id[:8]}...")
            return chat_id
    
    # 方法1.5: 直接遍历所有头部查找包含 chat-id 的
    for header_name, header_value in request.headers:
        if 'chat-id' in header_name.lower():
            logger.debug(f"🔍 Found chat_id in header '{header_name}': {header_value[:8]}...")
            return header_value
    
    # 方法2: 从请求体的 metadata 提取
    try:
        request_json = request.get_json() or {}
        metadata = request_json.get('metadata', {})
        chat_id = metadata.get('chat_id')
        if chat_id:
            logger.debug(f"🔍 Found chat_id in metadata: {chat_id[:8]}...")
            return chat_id
    except Exception as e:
        logger.debug(f"Failed to extract chat_id from metadata: {e}")
    
    # 方法3: 检查User-Agent，如果是OpenWebUI的后端，可能需要其他方式获取chat_id
    user_agent = request.headers.get('User-Agent', '')
    if 'aiohttp' in user_agent:
        logger.debug("🔍 Request from aiohttp (likely Open WebUI backend) but no chat_id header found")
        # 可以添加更多提取逻辑，比如从Authorization header或其他地方
    
    logger.debug("🔍 No chat_id found in request")
    return None

def extract_webui_user_id() -> Optional[str]:
    """从请求中提取 Open WebUI 的 user_id"""
    # 调试：查找用户ID相关头部
    logger.debug("🔍 Searching for user_id in headers:")
    for header_name, header_value in request.headers:
        if 'user' in header_name.lower():
            logger.debug(f"🔍   Found user-related header: '{header_name}' = '{header_value[:8]}...'")
    
    # 方法1: 从 HTTP Header 提取 (支持多种大小写形式)
    possible_headers = ['X-OpenWebUI-User-Id', 'x-openwebui-user-id', 'X-Openwebui-User-Id']
    
    for header_name in possible_headers:
        user_id = request.headers.get(header_name)
        if user_id:
            logger.debug(f"🔍 Found user_id in header '{header_name}': {user_id[:8]}...")
            return user_id
    
    # 方法2: 直接遍历所有头部查找包含 user-id 的
    for header_name, header_value in request.headers:
        if 'user-id' in header_name.lower():
            logger.debug(f"🔍 Found user_id in header '{header_name}': {header_value[:8]}...")
            return header_value
    
    # 方法3: 从请求体的 metadata 提取
    try:
        request_json = request.get_json() or {}
        metadata = request_json.get('metadata', {})
        user_id = metadata.get('user_id')
        if user_id:
            logger.debug(f"🔍 Found user_id in metadata: {user_id[:8]}...")
            return user_id
    except Exception as e:
        logger.debug(f"Failed to extract user_id from metadata: {e}")
    
    logger.debug("🔍 No user_id found in request")
    return None

def transform_openai_to_dify(openai_request, endpoint, webui_chat_id=None):
    """将OpenAI格式的请求转换为Dify格式"""
    
    if endpoint == "/chat/completions":
        messages = openai_request.get("messages", [])
        stream = openai_request.get("stream", False)
        
        # 处理 conversation_id 映射
        dify_conversation_id = None
        if webui_chat_id:
            dify_conversation_id = conversation_mapper.get_dify_conversation_id(webui_chat_id)
            if dify_conversation_id:
                conversation_mapper.update_last_used(webui_chat_id)  # 更新使用时间
            logger.info(f"🔄 WebUI chat_id: {webui_chat_id[:8]}... -> Dify conversation_id: {dify_conversation_id[:8] if dify_conversation_id else 'None'}...")
        
        # 提取用户ID - 优先级顺序
        user_id = (
            openai_request.get("user") or      # 1. OpenAI请求体中的user字段
            extract_webui_user_id() or         # 2. OpenWebUI头部中的user-id  
            "default_user"                     # 3. 默认值
        )
        
        logger.debug(f"👤 User ID resolved: {user_id[:8] if user_id != 'default_user' else user_id}...")
        
        dify_request = {
            "inputs": {},
            "query": messages[-1]["content"] if messages else "",
            "response_mode": "streaming" if stream else "blocking",
            "conversation_id": dify_conversation_id,
            "user": user_id
        }

        # 添加历史消息（只在没有 conversation_id 时使用，避免重复）
        if not dify_conversation_id and len(messages) > 1:
            history = []
            for msg in messages[:-1]:  # 除了最后一条消息
                history.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            dify_request["conversation_history"] = history
            logger.debug(f"📝 Added {len(history)} history messages (no conversation_id)")

        return dify_request
    
    return None

def transform_dify_to_openai(dify_response, model="claude-3-5-sonnet-v2", stream=False):
    """将Dify格式的响应转换为OpenAI格式"""
    
    if not stream:
        return {
            "id": dify_response.get("message_id", ""),
            "object": "chat.completion",
            "created": dify_response.get("created", int(time.time())),
            "model": model,  # 使用实际使用的模型
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": dify_response.get("answer", "")
                },
                "finish_reason": "stop"
            }]
        }
    else:
        # 流式响应的转换在stream_response函数中处理
        return dify_response

def create_openai_stream_response(content, message_id, model="claude-3-5-sonnet-v2"):
    """创建OpenAI格式的流式响应"""
    return {
        "id": message_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [{
            "index": 0,
            "delta": {
                "content": content
            },
            "finish_reason": None
        }]
    }

def update_conversation_mapping(webui_chat_id: str, dify_response: dict) -> None:
    """从 Dify 响应中提取 conversation_id 并更新映射"""
    if not webui_chat_id:
        return
    
    # 提取 conversation_id
    dify_conversation_id = dify_response.get("conversation_id")
    if dify_conversation_id and not conversation_mapper.has_mapping(webui_chat_id):
        conversation_mapper.set_mapping(webui_chat_id, dify_conversation_id)
        logger.info(f"🆕 New conversation mapping established")
    elif dify_conversation_id:
        logger.debug(f"✅ Conversation mapping already exists")

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    try:
        openai_request = request.get_json()
        logger.info(f"Received request: {json.dumps(openai_request, ensure_ascii=False)}")
        
        # 提取 Open WebUI chat_id 和 user_id
        webui_chat_id = extract_webui_chat_id()
        webui_user_id = extract_webui_user_id()
        
        if webui_chat_id:
            logger.info(f"🔗 Processing request for WebUI chat_id: {webui_chat_id[:8]}...")
        if webui_user_id:
            logger.info(f"👤 Processing request for WebUI user_id: {webui_user_id[:8]}...")
        
        model = openai_request.get("model", "claude-3-5-sonnet-v2")
        logger.info(f"Using model: {model}")
        
        # 验证模型是否支持
        api_key = get_api_key(model)
        if not api_key:
            error_msg = f"Model {model} is not supported. Available models: {', '.join(MODEL_TO_API_KEY.keys())}"
            logger.error(error_msg)
            return {
                "error": {
                    "message": error_msg,
                    "type": "invalid_request_error",
                    "code": "model_not_found"
                }
            }, 404
            
        dify_request = transform_openai_to_dify(openai_request, "/chat/completions", webui_chat_id)
        logger.info(f"Transformed request: {json.dumps(dify_request, ensure_ascii=False)}")
        
        if not dify_request:
            logger.error("Failed to transform request")
            return {
                "error": {
                    "message": "Invalid request format",
                    "type": "invalid_request_error",
                }
            }, 400

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        stream = openai_request.get("stream", False)
        dify_endpoint = f"{DIFY_API_BASE}/chat-messages"
        logger.info(f"Sending request to Dify endpoint: {dify_endpoint}, stream={stream}")

        if stream:
            def generate():
                client = get_http_client()
                
                def flush_chunk(chunk_data):
                    """Helper function to flush chunks immediately"""
                    return chunk_data.encode('utf-8')
                
                def calculate_delay(buffer_size):
                    """
                    根据缓冲区大小动态计算延迟
                    buffer_size: 缓冲区中剩余的字符数量
                    """
                    if buffer_size > 30:  # 缓冲区内容较多，快速输出
                        return 0.001  # 5ms延迟
                    elif buffer_size > 20:  # 中等数量，适中速度
                        return 0.002  # 10ms延迟
                    elif buffer_size > 10:  # 较少内容，稍慢速度
                        return 0.01  # 20ms延迟
                    else:  # 内容很少，使用较慢的速度
                        return 0.02  # 30ms延迟
                
                def send_char(char, message_id):
                    """Helper function to send single character"""
                    openai_chunk = {
                        "id": message_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": model,
                        "choices": [{
                            "index": 0,
                            "delta": {
                                "content": char
                            },
                            "finish_reason": None
                        }]
                    }
                    chunk_data = f"data: {json.dumps(openai_chunk)}\n\n"
                    return flush_chunk(chunk_data)
                
                # 初始化缓冲区
                output_buffer = []
                
                try:
                    # 移除预连接检查，直接进行流式请求
                    # 预连接检查可能过于严格，影响正常流式响应
                    
                    with client.stream(
                        'POST',
                        dify_endpoint,
                        json=dify_request,
                        headers={
                            **headers,
                            'Accept': 'text/event-stream',
                            'Cache-Control': 'no-cache',
                            'Connection': 'keep-alive'
                        }
                    ) as response:
                        generate.message_id = None
                        buffer = ""
                        
                        for raw_bytes in response.iter_raw():
                            if not raw_bytes:
                                continue
                                
                            try:
                                buffer += raw_bytes.decode('utf-8')
                                
                                while '\n' in buffer:
                                    line, buffer = buffer.split('\n', 1)
                                    line = line.strip()
                                    
                                    if not line or not line.startswith('data: '):
                                        continue
                                        
                                    try:
                                        json_str = line[6:]
                                        dify_chunk = json.loads(json_str)
                                        
                                        if dify_chunk.get("event") == "message" and "answer" in dify_chunk:
                                            current_answer = dify_chunk["answer"]
                                            if not current_answer:
                                                continue
                                                
                                            message_id = dify_chunk.get("message_id", "")
                                            if not generate.message_id:
                                                generate.message_id = message_id
                                                # 在流式响应的第一个消息中更新映射
                                                update_conversation_mapping(webui_chat_id, dify_chunk)
                                            
                                            # 将当前批次的字符添加到输出缓冲区
                                            for char in current_answer:
                                                output_buffer.append((char, generate.message_id))
                                            
                                            # 根据缓冲区大小动态调整输出速度
                                            while output_buffer:
                                                char, msg_id = output_buffer.pop(0)
                                                yield send_char(char, msg_id)
                                                # 根据剩余缓冲区大小计算延迟
                                                delay = calculate_delay(len(output_buffer))
                                                time.sleep(delay)
                                            
                                            # 立即继续处理下一个请求
                                            continue
                                        
                                        elif dify_chunk.get("event") == "message_end":
                                            # 快速输出剩余内容
                                            while output_buffer:
                                                char, msg_id = output_buffer.pop(0)
                                                yield send_char(char, msg_id)
                                                time.sleep(0.001)  # 固定使用最小延迟快速输出剩余内容
                                            
                                            final_chunk = {
                                                "id": generate.message_id,
                                                "object": "chat.completion.chunk",
                                                "created": int(time.time()),
                                                "model": model,
                                                "choices": [{
                                                    "index": 0,
                                                    "delta": {},
                                                    "finish_reason": "stop"
                                                }]
                                            }
                                            yield flush_chunk(f"data: {json.dumps(final_chunk)}\n\n")
                                            yield flush_chunk("data: [DONE]\n\n")
                                        
                                    except json.JSONDecodeError as e:
                                        logger.warning(f"JSON decode error in streaming response: {str(e)}, line: {json_str[:100]}...")
                                        continue
                                        
                            except Exception as e:
                                logger.error(f"Error processing chunk: {str(e)}")
                                continue

                except httpx.ConnectTimeout as e:
                    logger.error(f"Stream connection timeout: {e}")
                    yield flush_chunk(f"data: {{\"error\": \"Connection timeout: {str(e)}\"}}\n\n")
                    yield flush_chunk("data: [DONE]\n\n")
                except httpx.RequestError as e:
                    logger.error(f"Stream request error: {e}")
                    yield flush_chunk(f"data: {{\"error\": \"Request error: {str(e)}\"}}\n\n")
                    yield flush_chunk("data: [DONE]\n\n")
                except Exception as e:
                    logger.error(f"Unexpected stream error: {e}")
                    yield flush_chunk(f"data: {{\"error\": \"Internal error: {str(e)}\"}}\n\n")
                    yield flush_chunk("data: [DONE]\n\n")
                finally:
                    # 使用全局客户端，不需要手动关闭
                    pass

            return Response(
                stream_with_context(generate()),
                content_type='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache, no-transform',
                    'Connection': 'keep-alive',
                    'Transfer-Encoding': 'chunked',
                    'X-Accel-Buffering': 'no',
                    'Content-Encoding': 'none'
                },
                direct_passthrough=True
            )
        else:
            # 使用同步客户端处理非流式响应
            try:
                client = get_http_client()
                response = client.post(
                    dify_endpoint,
                    json=dify_request,
                    headers=headers
                )
                
                if response.status_code != 200:
                    error_msg = f"Dify API error: {response.text}"
                    logger.error(f"Request failed: {error_msg}")
                    return {
                        "error": {
                            "message": error_msg,
                            "type": "api_error",
                            "code": response.status_code
                        }
                    }, response.status_code

                dify_response = response.json()
                logger.info(f"Received response from Dify: {json.dumps(dify_response, ensure_ascii=False)}")
                
                # 更新会话映射
                update_conversation_mapping(webui_chat_id, dify_response)
                
                openai_response = transform_dify_to_openai(dify_response, model=model)
                return openai_response
                
            except httpx.TimeoutException as e:
                error_msg = f"Request timeout: {str(e)}"
                logger.error(f"Timeout error for model {model}: {error_msg}")
                return {
                    "error": {
                        "message": error_msg,
                        "type": "timeout_error",
                        "code": "request_timeout"
                    }
                }, 408
            except httpx.ConnectError as e:
                error_msg = f"Failed to connect to Dify API: {str(e)}"
                logger.error(f"Connection error for model {model}: {error_msg}")
                return {
                    "error": {
                        "message": error_msg,
                        "type": "connection_error", 
                        "code": "connection_failed"
                    }
                }, 503
            except httpx.RequestError as e:
                error_msg = f"Request failed: {str(e)}"
                logger.error(f"Request error for model {model}: {error_msg}")
                return {
                    "error": {
                        "message": error_msg,
                        "type": "api_error",
                        "code": "request_failed"
                    }
                }, 503

    except Exception as e:
        logger.exception("Unexpected error occurred")
        return {
            "error": {
                "message": str(e),
                "type": "internal_error",
            }
        }, 500

@app.route('/v1/models', methods=['GET'])
def list_models():
    """返回可用的模型列表"""
    logger.info("Listing available models")
    # 过滤掉没有API密钥的模型
    available_models = [
        model for model in AVAILABLE_MODELS 
        if MODEL_TO_API_KEY.get(model["id"])
    ]
    
    response = {
        "object": "list",
        "data": available_models
    }
    logger.info(f"Available models: {json.dumps(response, ensure_ascii=False)}")
    return response

@app.route('/v1/conversation/mappings', methods=['GET'])
def get_conversation_mappings():
    """获取当前的会话映射状态（调试用）"""
    stats = conversation_mapper.get_mapping_stats()
    return {
        "mapping_count": stats["total"],
        "oldest_mapping": stats["oldest"],
        "newest_mapping": stats["newest"],
        "timestamp": int(time.time())
    }

@app.route('/v1/conversation/cleanup', methods=['POST'])
def cleanup_old_conversations():
    """清理旧的会话映射"""
    max_age_days = request.json.get('max_age_days', 30) if request.is_json else 30
    removed_count = conversation_mapper.cleanup_old_mappings(max_age_days)
    return {
        "removed_count": removed_count,
        "max_age_days": max_age_days,
        "timestamp": int(time.time())
    }

if __name__ == '__main__':
    # 验证配置
    if not validate_startup_config():
        logger.error("❌ Startup aborted due to configuration errors")
        exit(1)
    
    host = os.getenv("SERVER_HOST", "127.0.0.1")
    port = int(os.getenv("SERVER_PORT", 5000))
    logger.info(f"🚀 Starting OpenDify server on http://{host}:{port}")
    
    try:
        app.run(debug=True, host=host, port=port)
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
    finally:
        cleanup_http_client()
