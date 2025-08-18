import sqlite3
import logging
import os
import time
from contextlib import contextmanager
from typing import Dict, Optional, List, Tuple

logger = logging.getLogger(__name__)

class ConversationMapper:
    """
    基于 SQLite 的会话映射管理器
    解决多进程环境下的并发访问问题
    """
    
    def __init__(self, db_path="data/conversation_mappings.db"):
        # 确保数据目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        
        # 初始化数据库
        self._init_database()
        logger.info(f"✅ ConversationMapper initialized with SQLite database: {db_path}")
    
    def _init_database(self) -> None:
        """初始化数据库表结构"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 首先检查表是否存在以及表结构
                cursor.execute('''
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='conversation_mappings'
                ''')
                table_exists = cursor.fetchone() is not None
                
                if table_exists:
                    # 检查表结构是否正确
                    cursor.execute('PRAGMA table_info(conversation_mappings)')
                    columns = [row[1] for row in cursor.fetchall()]
                    
                    required_columns = ['webui_chat_id', 'dify_conversation_id', 'created_at', 'last_used']
                    missing_columns = [col for col in required_columns if col not in columns]
                    
                    if missing_columns:
                        logger.warning(f"⚠️  Database table exists but missing columns: {missing_columns}")
                        logger.info("🔄 Recreating table with correct structure...")
                        
                        # 备份现有数据
                        cursor.execute('''
                            CREATE TABLE conversation_mappings_backup AS 
                            SELECT * FROM conversation_mappings
                        ''')
                        
                        # 删除旧表
                        cursor.execute('DROP TABLE conversation_mappings')
                        table_exists = False
                
                if not table_exists:
                    # 创建会话映射表
                    cursor.execute('''
                        CREATE TABLE conversation_mappings (
                            webui_chat_id TEXT PRIMARY KEY,
                            dify_conversation_id TEXT NOT NULL,
                            created_at INTEGER NOT NULL,
                            last_used INTEGER NOT NULL,
                            updated_at INTEGER DEFAULT (strftime('%s', 'now'))
                        )
                    ''')
                    logger.info("📋 Created conversation_mappings table")
                    
                    # 如果有备份数据，尝试迁移
                    cursor.execute('''
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name='conversation_mappings_backup'
                    ''')
                    if cursor.fetchone():
                        try:
                            # 尝试从备份迁移数据
                            current_time = int(time.time())
                            cursor.execute('''
                                INSERT INTO conversation_mappings (webui_chat_id, dify_conversation_id, created_at, last_used)
                                SELECT 
                                    webui_chat_id,
                                    dify_conversation_id,
                                    COALESCE(created_at, ?) as created_at,
                                    COALESCE(last_used, created_at, ?) as last_used
                                FROM conversation_mappings_backup
                            ''', (current_time, current_time))
                            
                            migrated_count = cursor.rowcount
                            logger.info(f"📦 Migrated {migrated_count} records from backup")
                            
                            # 删除备份表
                            cursor.execute('DROP TABLE conversation_mappings_backup')
                            
                        except Exception as e:
                            logger.error(f"❌ Failed to migrate backup data: {e}")
                            # 删除备份表
                            cursor.execute('DROP TABLE IF EXISTS conversation_mappings_backup')
                
                # 安全地创建索引
                try:
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_last_used 
                        ON conversation_mappings(last_used)
                    ''')
                    
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_created_at 
                        ON conversation_mappings(created_at)
                    ''')
                    logger.debug("📊 Created database indexes")
                    
                except Exception as e:
                    logger.warning(f"⚠️  Failed to create indexes: {e}")
                
                conn.commit()
                
                # 获取现有映射数量
                cursor.execute('SELECT COUNT(*) FROM conversation_mappings')
                count = cursor.fetchone()[0]
                logger.info(f"📂 Database initialized with {count} existing conversation mappings")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise
    
    @contextmanager
    def _get_connection(self):
        """
        获取数据库连接的上下文管理器
        确保连接正确关闭
        """
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=30.0,  # 30秒超时
                check_same_thread=False  # 允许多线程访问
            )
            # 启用 WAL 模式提高并发性能
            conn.execute('PRAGMA journal_mode=WAL')
            # 启用外键约束
            conn.execute('PRAGMA foreign_keys=ON')
            # 设置忙等待超时
            conn.execute('PRAGMA busy_timeout=30000')
            
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def get_dify_conversation_id(self, webui_chat_id: str) -> Optional[str]:
        """根据 Open WebUI chat_id 获取对应的 Dify conversation_id"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT dify_conversation_id FROM conversation_mappings WHERE webui_chat_id = ?',
                    (webui_chat_id,)
                )
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to get dify_conversation_id for {webui_chat_id[:8]}...: {e}")
            return None
    
    def set_mapping(self, webui_chat_id: str, dify_conversation_id: str) -> None:
        """设置映射关系，使用 UPSERT 避免重复"""
        try:
            current_time = int(time.time())
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 使用 INSERT OR REPLACE 实现 UPSERT
                cursor.execute('''
                    INSERT OR REPLACE INTO conversation_mappings 
                    (webui_chat_id, dify_conversation_id, created_at, last_used, updated_at)
                    VALUES (?, ?, 
                        COALESCE((SELECT created_at FROM conversation_mappings WHERE webui_chat_id = ?), ?),
                        ?, ?)
                ''', (
                    webui_chat_id, 
                    dify_conversation_id,
                    webui_chat_id,  # 用于 COALESCE 查询
                    current_time,   # 新记录的 created_at
                    current_time,   # last_used
                    current_time    # updated_at
                ))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"🔗 Mapped WebUI chat_id {webui_chat_id[:8]}... to Dify conversation_id {dify_conversation_id[:8]}...")
                
        except Exception as e:
            logger.error(f"Failed to set mapping for {webui_chat_id[:8]}...: {e}")
    
    def has_mapping(self, webui_chat_id: str) -> bool:
        """检查是否存在映射关系"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT 1 FROM conversation_mappings WHERE webui_chat_id = ? LIMIT 1',
                    (webui_chat_id,)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Failed to check mapping for {webui_chat_id[:8]}...: {e}")
            return False
    
    def update_last_used(self, webui_chat_id: str) -> None:
        """更新映射的最后使用时间"""
        try:
            current_time = int(time.time())
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE conversation_mappings 
                    SET last_used = ?, updated_at = ?
                    WHERE webui_chat_id = ?
                ''', (current_time, current_time, webui_chat_id))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.debug(f"📝 Updated last_used for {webui_chat_id[:8]}...")
                
        except Exception as e:
            logger.error(f"Failed to update last_used for {webui_chat_id[:8]}...: {e}")
    
    def get_mapping_count(self) -> int:
        """获取当前映射数量"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM conversation_mappings')
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Failed to get mapping count: {e}")
            return 0
    
    def cleanup_old_mappings(self, max_age_days: int = 30) -> int:
        """清理超过指定天数的映射"""
        try:
            cutoff_time = int(time.time()) - (max_age_days * 24 * 60 * 60)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 先查询要删除的记录数
                cursor.execute(
                    'SELECT COUNT(*) FROM conversation_mappings WHERE last_used < ?',
                    (cutoff_time,)
                )
                count_to_remove = cursor.fetchone()[0]
                
                if count_to_remove > 0:
                    # 删除过期记录
                    cursor.execute(
                        'DELETE FROM conversation_mappings WHERE last_used < ?',
                        (cutoff_time,)
                    )
                    conn.commit()
                    
                    logger.info(f"🧹 Cleaned up {count_to_remove} old mappings (older than {max_age_days} days)")
                
                return count_to_remove
                
        except Exception as e:
            logger.error(f"Failed to cleanup old mappings: {e}")
            return 0
    
    def get_mapping_stats(self) -> dict:
        """获取映射统计信息"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取基本统计
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total,
                        MIN(created_at) as oldest,
                        MAX(created_at) as newest,
                        AVG(last_used) as avg_last_used
                    FROM conversation_mappings
                ''')
                
                result = cursor.fetchone()
                if result[0] == 0:  # 没有记录
                    return {
                        "total": 0,
                        "oldest": None,
                        "newest": None,
                        "avg_last_used": None
                    }
                
                return {
                    "total": result[0],
                    "oldest": result[1],
                    "newest": result[2],
                    "avg_last_used": int(result[3]) if result[3] else None
                }
                
        except Exception as e:
            logger.error(f"Failed to get mapping stats: {e}")
            return {"total": 0, "oldest": None, "newest": None, "avg_last_used": None}
    
    def get_recent_mappings(self, limit: int = 10) -> List[Tuple[str, str, int, int]]:
        """获取最近的映射记录（用于调试）"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT webui_chat_id, dify_conversation_id, created_at, last_used
                    FROM conversation_mappings
                    ORDER BY last_used DESC
                    LIMIT ?
                ''', (limit,))
                
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"Failed to get recent mappings: {e}")
            return []
    
    def optimize_database(self) -> None:
        """优化数据库性能"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 分析表以更新统计信息
                cursor.execute('ANALYZE conversation_mappings')
                
                # 清理WAL文件
                cursor.execute('PRAGMA wal_checkpoint(TRUNCATE)')
                
                conn.commit()
                logger.info("🔧 Database optimization completed")
                
        except Exception as e:
            logger.error(f"Failed to optimize database: {e}")
    
    def get_database_info(self) -> dict:
        """获取数据库信息（用于监控）"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取数据库大小
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                db_size = cursor.fetchone()[0]
                
                # 获取WAL模式状态
                cursor.execute("PRAGMA journal_mode")
                journal_mode = cursor.fetchone()[0]
                
                # 获取表信息
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                return {
                    "database_path": self.db_path,
                    "database_size_bytes": db_size,
                    "journal_mode": journal_mode,
                    "tables": tables,
                    "mapping_count": self.get_mapping_count()
                }
                
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {"error": str(e)}