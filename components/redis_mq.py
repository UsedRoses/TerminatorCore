from abc import ABC, abstractmethod

import redis
import threading
from typing import Callable, Dict

from django_redis import get_redis_connection

from TerminatorBaseCore.entity.design_patterns import Singleton

# Redis 客户端
redis_client = get_redis_connection("default")


# 通用生产者类
class RedisProducer:

    @staticmethod
    def send_message(topic: str, message: Dict[str, str]) -> None:
        """
        发送消息到指定主题
        """
        redis_client.xadd(topic, message)


# 消费者基类
class RedisBaseConsumer(ABC, Singleton):

    @abstractmethod
    def consume(self, message_id: str, message: Dict[str, str]) -> None:
        """
        子类需要实现的消费逻辑
        """
        raise NotImplementedError("Subclasses must implement this method")


def process_pending_messages(topic: str, group_name: str, consumer_cls: Callable, retry_threshold: int = 3):
    """
    定期处理未确认的消息
    """
    consumer_instance = consumer_cls()
    while True:
        try:
            # 检查未确认消息
            pending_info = redis_client.xpending(topic, group_name)
            print("检查未确认的消息")
            print(group_name)
            print(pending_info)
            if pending_info["pending"] > 0:
                # 获取未确认的消息 ID 范围
                pending_messages = redis_client.xrange(
                    topic, min=pending_info["min"], max=pending_info["max"]
                )
                for msg_id, msg_data in pending_messages:
                    try:
                        # 消费失败的重试逻辑
                        retry_count = int(msg_data.get("retry", 0))
                        if retry_count >= retry_threshold:
                            print(f"Skipping message {msg_id} after {retry_count} retries.")
                            redis_client.xack(topic, group_name, msg_id)  # 放弃确认
                            continue

                        # 尝试重新消费
                        consumer_instance.consume(msg_id, msg_data)
                        redis_client.xack(topic, group_name, msg_id)  # 确认消息
                    except Exception as e:
                        print(f"Retry failed for message {msg_id}: {e}")
                        redis_client.xadd(topic, {**msg_data, "retry": retry_count + 1})  # 增加重试计数
        except Exception as e:
            print(f"Error in pending message processing for topic {topic}: {e}")

        # 每隔 60 秒检查一次
        threading.Event().wait(60)


# 消费者运行逻辑
def run_consumer(topic: str, consumer_cls: Callable):
    """
    消费者运行逻辑，只处理新消息
    """
    group_name = f"{topic}_group"
    consumer_name = f"{topic}_consumer"

    # 确保消费组存在
    try:
        redis_client.xgroup_create(topic, group_name, mkstream=True)
    except redis.exceptions.ResponseError:
        pass  # 消费组已存在

    # 创建消费者实例
    consumer_instance = consumer_cls()

    while True:
        try:
            # 读取新消息（阻塞）
            messages = redis_client.xreadgroup(
                group_name, consumer_name, {topic: ">"}, count=1, block=10000
            )

            if messages:  # 处理新消息
                for stream, msgs in messages:
                    for msg_id, msg_data in msgs:
                        try:
                            consumer_instance.consume(msg_id, msg_data)
                            redis_client.xack(topic, group_name, msg_id)  # 确认消息
                        except Exception as e:
                            print(f"Error consuming message {msg_id}: {e}")
        except Exception as e:
            print(f"Error in consumer loop for topic {topic}: {e}")


# 消费者装饰器
def consumer(topic: str, retry_threshold: int = 3):
    """
    装饰器，用于注册消费者
    """

    def decorator(cls):
        # 启动主线程：消费新消息
        threading.Thread(target=run_consumer, args=(topic, cls)).start()

        # 启动辅助线程：定期处理未确认消息
        threading.Thread(target=process_pending_messages, args=(topic, f"{topic}_group", cls, retry_threshold)).start()

        return cls

    return decorator
