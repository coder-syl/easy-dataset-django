# coding=utf-8
"""
    @project: maxkb
    @Author：虎
    @file： embedding_config.py
    @date：2023/10/23 16:03
    @desc:
"""
import threading
import time

from common.cache.mem_cache import MemCache

_lock = threading.Lock()
locks = {}


class ModelManage:
    # 使用MemCache缓存模型实例，缓存名称为'model'
    cache = MemCache('model', {})
    # 记录上次清理缓存的时间
    up_clear_time = time.time()

    @staticmethod
    def _get_lock(_id):
        # 获取指定ID的锁对象
        lock = locks.get(_id)
        if lock is None:
            # 如果锁不存在，使用全局锁保护创建过程
            with _lock:
                lock = locks.get(_id)
                if lock is None:
                    # 创建新的锁对象并存储
                    lock = threading.Lock()
                    locks[_id] = lock

        return lock

    @staticmethod
    def get_model(_id, get_model):
        # 尝试从缓存获取模型实例
        model_instance = ModelManage.cache.get(_id)
        if model_instance is None:
            # 如果缓存中没有，使用锁保护模型创建过程
            lock = ModelManage._get_lock(_id)
            with lock:
                model_instance = ModelManage.cache.get(_id)
                if model_instance is None:
                    # 创建新的模型实例并缓存8小时
                    model_instance = get_model(_id)
                    ModelManage.cache.set(_id, model_instance, timeout=60 * 60 * 8)
        else:
            if model_instance.is_cache_model():
                # 如果是可缓存的模型，更新缓存时间
                ModelManage.cache.touch(_id, timeout=60 * 60 * 8)
            else:
                # 如果是不可缓存的模型，重新获取并更新缓存
                model_instance = get_model(_id)
                ModelManage.cache.set(_id, model_instance, timeout=60 * 60 * 8)
        # 清理过期缓存
        ModelManage.clear_timeout_cache()
        return model_instance

    @staticmethod
    def clear_timeout_cache():
        # 每小时检查一次是否需要清理过期缓存
        if time.time() - ModelManage.up_clear_time > 60 * 60:
            # 在新线程中异步清理过期数据
            threading.Thread(target=lambda: ModelManage.cache.clear_timeout_data()).start()
            ModelManage.up_clear_time = time.time()

    @staticmethod
    def delete_key(_id):
        # 从缓存中删除指定ID的模型实例
        if ModelManage.cache.has_key(_id):
            ModelManage.cache.delete(_id)


class VectorStore:
    from embedding.vector.pg_vector import PGVector
    from embedding.vector.base_vector import BaseVectorStore
    instance_map = {
        'pg_vector': PGVector,
    }
    instance = None

    @staticmethod
    def get_embedding_vector() -> BaseVectorStore:
        from embedding.vector.pg_vector import PGVector
        if VectorStore.instance is None:
            from smartdoc.const import CONFIG
            vector_store_class = VectorStore.instance_map.get(CONFIG.get("VECTOR_STORE_NAME"),
                                                              PGVector)
            VectorStore.instance = vector_store_class()
        return VectorStore.instance
