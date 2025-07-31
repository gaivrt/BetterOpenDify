#!/usr/bin/env python3
"""
数据迁移脚本：从 JSON 文件迁移到 SQLite 数据库
用于从旧版本的 ConversationMapper 迁移到新的 SQLite 版本
"""

import json
import os
import sys
import logging
from conversation_mapper_sqlite import ConversationMapper

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def migrate_json_to_sqlite(json_file_path="data/conversation_mappings.json", 
                          sqlite_db_path="data/conversation_mappings.db"):
    """
    将 JSON 格式的会话映射迁移到 SQLite 数据库
    
    Args:
        json_file_path: 原 JSON 文件路径
        sqlite_db_path: 目标 SQLite 数据库路径
    """
    
    # 检查 JSON 文件是否存在
    if not os.path.exists(json_file_path):
        logger.info(f"📂 JSON 文件不存在: {json_file_path}")
        logger.info("✅ 无需迁移，可以直接使用 SQLite 版本")
        return True
    
    # 检查 SQLite 数据库是否已存在
    if os.path.exists(sqlite_db_path):
        logger.warning(f"⚠️  SQLite 数据库已存在: {sqlite_db_path}")
        response = input("是否要覆盖现有数据库？(y/N): ").strip().lower()
        if response != 'y':
            logger.info("❌ 迁移已取消")
            return False
        
        # 备份现有数据库
        backup_path = sqlite_db_path + ".backup"
        os.rename(sqlite_db_path, backup_path)
        logger.info(f"📋 已备份现有数据库到: {backup_path}")
    
    try:
        # 读取 JSON 数据
        logger.info(f"📖 正在读取 JSON 文件: {json_file_path}")
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        logger.info(f"📊 找到 {len(json_data)} 条映射记录")
        
        if not json_data:
            logger.info("✅ JSON 文件为空，无需迁移")
            return True
        
        # 创建 SQLite 数据库
        logger.info(f"🗄️  创建 SQLite 数据库: {sqlite_db_path}")
        mapper = ConversationMapper(sqlite_db_path)
        
        # 迁移数据
        migrated_count = 0
        errors = 0
        
        for webui_chat_id, mapping_info in json_data.items():
            try:
                if isinstance(mapping_info, dict):
                    # 新格式（包含 created_at, last_used 等信息）
                    dify_conversation_id = mapping_info.get('dify_conversation_id')
                    if dify_conversation_id:
                        mapper.set_mapping(webui_chat_id, dify_conversation_id)
                        migrated_count += 1
                    else:
                        logger.warning(f"⚠️  跳过缺少 dify_conversation_id 的记录: {webui_chat_id[:8]}...")
                        errors += 1
                elif isinstance(mapping_info, str):
                    # 旧格式（直接存储 dify_conversation_id）
                    mapper.set_mapping(webui_chat_id, mapping_info)
                    migrated_count += 1
                else:
                    logger.warning(f"⚠️  跳过格式不正确的记录: {webui_chat_id[:8]}...")
                    errors += 1
                    
            except Exception as e:
                logger.error(f"❌ 迁移记录失败 {webui_chat_id[:8]}...: {e}")
                errors += 1
        
        # 验证迁移结果
        final_stats = mapper.get_mapping_stats()
        
        logger.info("📊 迁移结果:")
        logger.info(f"   - 成功迁移: {migrated_count} 条记录")
        logger.info(f"   - 迁移错误: {errors} 条记录")
        logger.info(f"   - 数据库记录总数: {final_stats['total']}")
        
        if final_stats['total'] == migrated_count:
            logger.info("✅ 数据迁移成功！")
            
            # 备份原 JSON 文件
            json_backup_path = json_file_path + ".backup"
            os.rename(json_file_path, json_backup_path)
            logger.info(f"📋 已备份原 JSON 文件到: {json_backup_path}")
            
            # 显示数据库信息
            db_info = mapper.get_database_info()
            logger.info(f"🗄️  数据库信息:")
            logger.info(f"   - 路径: {db_info.get('database_path')}")
            logger.info(f"   - 大小: {db_info.get('database_size_bytes', 0)} 字节")
            logger.info(f"   - 模式: {db_info.get('journal_mode', 'unknown')}")
            
            return True
        else:
            logger.error("❌ 数据验证失败，迁移可能不完整")
            return False
            
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON 文件格式错误: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ 迁移过程中发生错误: {e}")
        return False

def main():
    """主函数"""
    logger.info("🚀 OpenDify 数据库迁移工具")
    logger.info("从 JSON 文件迁移到 SQLite 数据库")
    logger.info("-" * 50)
    
    # 解析命令行参数
    json_path = "data/conversation_mappings.json"
    sqlite_path = "data/conversation_mappings.db"
    
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    if len(sys.argv) > 2:
        sqlite_path = sys.argv[2]
    
    logger.info(f"📂 JSON 文件: {json_path}")
    logger.info(f"🗄️  SQLite 数据库: {sqlite_path}")
    logger.info("-" * 50)
    
    # 确保目录存在
    os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
    
    # 执行迁移
    success = migrate_json_to_sqlite(json_path, sqlite_path)
    
    if success:
        logger.info("🎉 迁移完成！")
        logger.info("💡 提示:")
        logger.info("   - 现在可以使用新的 SQLite ConversationMapper")
        logger.info("   - 支持多进程并发安全")
        logger.info("   - 更好的性能和可靠性")
        logger.info("   - 可以删除备份文件如果确认无误")
        sys.exit(0)
    else:
        logger.error("❌ 迁移失败")
        sys.exit(1)

if __name__ == "__main__":
    main()