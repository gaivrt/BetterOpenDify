#!/usr/bin/env python3
"""
多进程并发测试 - 验证 SQLite ConversationMapper 的并发安全性
"""

import os
import sys
import time
import uuid
import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
import tempfile
import shutil

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from conversation_mapper_sqlite import ConversationMapper

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - PID:%(process)d - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def worker_task(worker_id: int, db_path: str, operations_per_worker: int):
    """
    工作进程任务：模拟真实的并发操作
    """
    logger.info(f"Worker {worker_id} started with PID {os.getpid()}")
    
    try:
        # 每个进程创建自己的 ConversationMapper 实例
        mapper = ConversationMapper(db_path)
        
        results = {
            'worker_id': worker_id,
            'pid': os.getpid(),
            'operations_completed': 0,
            'errors': 0,
            'mapping_conflicts': 0
        }
        
        for i in range(operations_per_worker):
            try:
                # 生成唯一的标识符
                chat_id = f"chat-{worker_id}-{i}-{uuid.uuid4().hex[:8]}"
                conv_id = f"conv-{worker_id}-{i}-{uuid.uuid4().hex[:8]}"
                
                # 测试基本操作
                # 1. 设置映射
                mapper.set_mapping(chat_id, conv_id)
                
                # 2. 检查映射是否存在
                if not mapper.has_mapping(chat_id):
                    results['mapping_conflicts'] += 1
                    logger.warning(f"Worker {worker_id}: Mapping not found immediately after creation")
                
                # 3. 获取映射
                retrieved_conv_id = mapper.get_dify_conversation_id(chat_id)
                if retrieved_conv_id != conv_id:
                    results['mapping_conflicts'] += 1
                    logger.warning(f"Worker {worker_id}: Retrieved conv_id mismatch: {retrieved_conv_id} != {conv_id}")
                
                # 4. 更新最后使用时间
                mapper.update_last_used(chat_id)
                
                # 5. 每10次操作检查一次统计信息
                if i % 10 == 0:
                    stats = mapper.get_mapping_stats()
                    logger.debug(f"Worker {worker_id}: Current stats - Total: {stats['total']}")
                
                results['operations_completed'] += 1
                
                # 模拟一些处理延迟
                time.sleep(0.001)
                
            except Exception as e:
                results['errors'] += 1
                logger.error(f"Worker {worker_id} operation {i} failed: {e}")
        
        # 最终统计
        final_stats = mapper.get_mapping_stats()
        results['final_mapping_count'] = final_stats['total']
        
        logger.info(f"Worker {worker_id} completed: {results['operations_completed']} operations, {results['errors']} errors")
        return results
        
    except Exception as e:
        logger.error(f"Worker {worker_id} failed: {e}")
        return {
            'worker_id': worker_id,
            'pid': os.getpid(),
            'operations_completed': 0,
            'errors': 1,
            'error_message': str(e)
        }

def test_concurrent_access():
    """测试并发访问"""
    logger.info("=== 开始并发访问测试 ===")
    
    # 创建临时数据库文件
    temp_dir = tempfile.mkdtemp(prefix="opendify_test_")
    db_path = os.path.join(temp_dir, "test_conversations.db")
    
    try:
        # 测试参数
        num_workers = 4  # 进程数
        operations_per_worker = 50  # 每个进程的操作次数
        
        logger.info(f"启动 {num_workers} 个进程，每个进程执行 {operations_per_worker} 次操作")
        logger.info(f"使用数据库: {db_path}")
        
        start_time = time.time()
        
        # 使用进程池执行并发测试
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            # 提交任务
            futures = []
            for worker_id in range(num_workers):
                future = executor.submit(
                    worker_task, 
                    worker_id, 
                    db_path, 
                    operations_per_worker
                )
                futures.append(future)
            
            # 收集结果
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=60)  # 60秒超时
                    results.append(result)
                except Exception as e:
                    logger.error(f"Worker failed with exception: {e}")
                    results.append({'error': str(e)})
        
        end_time = time.time()
        
        # 分析结果
        logger.info("=== 测试结果分析 ===")
        total_operations = sum(r.get('operations_completed', 0) for r in results)
        total_errors = sum(r.get('errors', 0) for r in results)
        total_conflicts = sum(r.get('mapping_conflicts', 0) for r in results)
        
        logger.info(f"总耗时: {end_time - start_time:.2f} 秒")
        logger.info(f"总操作数: {total_operations}")
        logger.info(f"总错误数: {total_errors}")
        logger.info(f"映射冲突数: {total_conflicts}")
        logger.info(f"操作成功率: {(total_operations / (num_workers * operations_per_worker)) * 100:.2f}%")
        
        # 验证最终数据一致性
        final_mapper = ConversationMapper(db_path)
        final_stats = final_mapper.get_mapping_stats()
        expected_total = num_workers * operations_per_worker
        
        logger.info(f"预期映射总数: {expected_total}")
        logger.info(f"实际映射总数: {final_stats['total']}")
        logger.info(f"数据一致性: {'✅ 通过' if final_stats['total'] == expected_total else '❌ 失败'}")
        
        # 测试数据库信息
        db_info = final_mapper.get_database_info()
        logger.info(f"数据库大小: {db_info.get('database_size_bytes', 0)} 字节")
        logger.info(f"日志模式: {db_info.get('journal_mode', 'unknown')}")
        
        return {
            'success': total_errors == 0 and total_conflicts == 0,
            'total_operations': total_operations,
            'total_errors': total_errors,
            'total_conflicts': total_conflicts,
            'execution_time': end_time - start_time,
            'data_consistency': final_stats['total'] == expected_total
        }
        
    finally:
        # 清理临时文件
        try:
            shutil.rmtree(temp_dir)
            logger.info(f"已清理临时文件: {temp_dir}")
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")

def test_database_features():
    """测试数据库特性"""
    logger.info("=== 数据库特性测试 ===")
    
    temp_dir = tempfile.mkdtemp(prefix="opendify_feature_test_")
    db_path = os.path.join(temp_dir, "feature_test.db")
    
    try:
        mapper = ConversationMapper(db_path)
        
        # 测试基本操作
        test_chat_id = "test-chat-123"
        test_conv_id = "test-conv-456"
        
        # 设置映射
        mapper.set_mapping(test_chat_id, test_conv_id)
        logger.info("✅ 设置映射成功")
        
        # 获取映射
        retrieved = mapper.get_dify_conversation_id(test_chat_id)
        assert retrieved == test_conv_id, f"映射不匹配: {retrieved} != {test_conv_id}"
        logger.info("✅ 获取映射成功")
        
        # 检查映射存在
        assert mapper.has_mapping(test_chat_id), "映射应该存在"
        logger.info("✅ 映射存在检查成功")
        
        # 更新最后使用时间
        mapper.update_last_used(test_chat_id)
        logger.info("✅ 更新最后使用时间成功")
        
        # 获取统计信息
        stats = mapper.get_mapping_stats()
        assert stats['total'] == 1, f"统计不正确: {stats['total']} != 1"
        logger.info(f"✅ 统计信息正确: {stats}")
        
        # 获取最近映射
        recent = mapper.get_recent_mappings(5)
        assert len(recent) == 1, f"最近映射数量不正确: {len(recent)} != 1"
        logger.info(f"✅ 最近映射功能正常: {len(recent)} 条记录")
        
        # 测试清理功能
        time.sleep(1)  # 等待1秒
        cleaned = mapper.cleanup_old_mappings(max_age_days=0)  # 清理所有
        assert cleaned == 1, f"清理数量不正确: {cleaned} != 1"
        logger.info("✅ 清理功能正常")
        
        # 验证清理后的状态
        final_stats = mapper.get_mapping_stats()
        assert final_stats['total'] == 0, f"清理后统计不正确: {final_stats['total']} != 0"
        logger.info("✅ 清理后状态正确")
        
        # 测试数据库优化
        mapper.optimize_database()
        logger.info("✅ 数据库优化成功")
        
        # 测试数据库信息
        db_info = mapper.get_database_info()
        assert 'database_size_bytes' in db_info, "数据库信息应包含大小"
        assert 'journal_mode' in db_info, "数据库信息应包含日志模式"
        logger.info(f"✅ 数据库信息获取成功: {db_info}")
        
        logger.info("=== 所有数据库特性测试通过 ===")
        return True
        
    except Exception as e:
        logger.error(f"数据库特性测试失败: {e}")
        return False
        
    finally:
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"清理测试文件失败: {e}")

def main():
    """主测试函数"""
    logger.info("开始 OpenDify SQLite ConversationMapper 并发安全测试")
    
    # 测试数据库基本特性
    logger.info("\n" + "="*50)
    feature_test_passed = test_database_features()
    
    if not feature_test_passed:
        logger.error("数据库特性测试失败，跳过并发测试")
        return False
    
    # 测试并发访问安全性
    logger.info("\n" + "="*50)
    concurrent_result = test_concurrent_access()
    
    # 最终总结
    logger.info("\n" + "="*50)
    logger.info("=== 测试总结 ===")
    
    if feature_test_passed and concurrent_result['success'] and concurrent_result['data_consistency']:
        logger.info("🎉 所有测试通过！SQLite ConversationMapper 可以安全用于多进程环境")
        logger.info("主要改进:")
        logger.info("  ✅ 使用 SQLite 数据库替代 JSON 文件存储")
        logger.info("  ✅ 数据库自动处理并发访问和事务")
        logger.info("  ✅ WAL 模式提高并发性能")
        logger.info("  ✅ 移除了不必要的线程锁")
        logger.info("  ✅ 支持多进程安全访问")
        return True
    else:
        logger.error("❌ 测试失败，需要进一步调试")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)