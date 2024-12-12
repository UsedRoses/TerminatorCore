from abc import abstractmethod, ABC
import time
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django_redis import get_redis_connection
import json

from TerminatorBaseCore.common.constant import Dead_Letter_Queue
from TerminatorBaseCore.common.error_code import ERROR_CODE
from TerminatorBaseCore.components.consumer_register import _register_consumer
from TerminatorBaseCore.entity.exception import ServiceException
from TerminatorBaseCore.entity.message import MessageRecord
from TerminatorBaseCore.utils.ip_util import get_ipv4_to_int


class RedisProducer:
    """
    主题设置
    """
    class _TopicSetter:
        """
        设置消息体
        """
        class _MessageSetter:
            def __init__(self, producer):
                self._producer = producer

            def send(self):
                if self._producer._redis_available:

                    """发送消息到 Redis 队列"""

                    message_body = self._producer._message_body
                    # 将消息内容序列化为 JSON 字符串
                    if isinstance(message_body, dict):
                        message_data = json.dumps(message_body)
                    elif isinstance(message_body, str):
                        message_data = message_body
                    else:
                        raise ServiceException(message="Unknown message_body type", code=ERROR_CODE)

                    record = MessageRecord(topic=self._producer._topic, key=self._producer._key,
                                           message_body=message_body, producer_ip=get_ipv4_to_int())
                    record.save()

                    message = {
                        "id": record.id,
                        "key": record.key,
                        "message_body": message_data
                    }
                    message = json.dumps(message)
                    # 使用 Redis 的 LPUSH 将消息推送到队列
                    # 拼上项目名,避免redis混用
                    project_name = getattr(settings, 'PROJECT_NAME', "T800")
                    topic = f'{project_name}:{self._producer.topic}'
                    self._producer._redis.lpush(topic, message)

                    # 打印发送的消息
                    print(f"Message sent to topic {self._producer.topic}: {self._producer.message}")
                    return record.pk
                else:
                    raise ServiceException(message="redis service not started", code=ERROR_CODE)

            def send_delay(self, delay_seconds):
                if self._producer._redis_available:

                    """发送消息到 Redis 队列"""

                    # 计算延迟时间的 Unix 时间戳
                    delay_timestamp = time.time() + delay_seconds

                    message_body = self._producer._message_body
                    # 将消息内容序列化为 JSON 字符串
                    if isinstance(message_body, dict):
                        message_data = json.dumps(message_body)
                    elif isinstance(message_body, str):
                        message_data = message_body
                    else:
                        raise ServiceException(message="Unknown message_body type", code=ERROR_CODE)

                    record = MessageRecord(topic=self._producer._topic + "_delay", key=self._producer._key,
                                           message_body=message_body, producer_ip=get_ipv4_to_int())
                    record.save()

                    message = {
                        "id": record.id,
                        "key": record.key,
                        "message_body": message_data
                    }
                    message = json.dumps(message)
                    # 使用 Redis 的 LPUSH 将消息推送到队列
                    # 拼上项目名,避免redis混用
                    project_name = getattr(settings, 'PROJECT_NAME', "T800")
                    topic = f'{project_name}:{self._producer.topic}_delay'
                    self._producer._redis.zadd(topic, {message: delay_timestamp})

                    # 打印发送的消息
                    print(f"Message sent to topic {self._producer.topic}: {self._producer.message}")
                    return record.pk
                else:
                    raise ServiceException(message="redis service not started", code=ERROR_CODE)
        def __init__(self, producer):
            # 持有 Producer 实例
            self._producer = producer

        def setMessage(self, message_body, key: str = None) -> _MessageSetter:
            """设置消息内容，并返回 MessageSetter 对象"""
            self._producer._message_body = message_body
            self._producer._key = key
            return self._MessageSetter(self._producer)  # 返回 MessageSetter 对象

    def __init__(self):
        try:
            # 尝试获取 Redis 连接
            self._redis = get_redis_connection("default")
            # 测试连接
            self._redis.ping()
            self._redis_available = True
        except (ImportError, ConnectionError):
            # Redis 未安装或不可用
            self._redis_available = False

    def setTopic(self, topic: str) -> _TopicSetter:
        self._topic = topic
        return RedisProducer._TopicSetter(self)


class RedisConsumer(ABC):

    def __init__(self):
        try:
            # 尝试获取 Redis 连接
            self._redis = get_redis_connection("default")
            # 测试连接
            self._redis.ping()
            self._redis_available = True
        except (ImportError, ConnectionError):
            # Redis 未安装或不可用
            self._redis_available = False

    def __init_subclass__(cls, **kwargs):
        """动态注册子类"""
        super().__init_subclass__(**kwargs)
        _register_consumer(cls)

    @property
    @abstractmethod
    def topic(self) -> str:
        return ''

    @abstractmethod
    def process_message(self, key: str, message, call_back=None):
        """
        开发者必须实现这个方法来处理消息
        """
        pass

    def consume(self):
        if not self._redis_available:
            return
        """
        消费消息队列
        """

        while True:
            message = self._redis.blpop(self.topic)
            if message:
                message_data = json.loads(message[1])
                message_id = message_data.get("id", 0)
                key = message_data.get("key", None)
                message_body_ori = message_data.get("message_body", '')
                call_back = message_data.get("call_back", None)

                message_body = try_parse_json(message_body_ori)

                message_record = MessageRecord.objects.get(id=message_id)
                if message_record:
                    message_record.consume_attempts = message_record.consume_attempts + 1
                    message_record.consume_time = timezone.now()
                    message_record.consumer_ip = get_ipv4_to_int()
                try:
                    with transaction.atomic():
                        self.process_message(key, message_body, call_back)

                    if message_record:
                        message_record.status = MessageRecord.Status.SUCCESS
                        message_record.save()
                except Exception as e:
                    # 加入死信队列
                    if message_record:
                        message_record.status = MessageRecord.Status.RETRY
                        message_record.failure_reason = str(e)

                        if message_record.consume_attempts < 3:
                            delay = message_record.consume_attempts * 60
                            # 重试
                            message_data.update({"call_back": self.topic})
                            dead_message = json.dumps(message_data)
                            RedisProducer().setTopic(Dead_Letter_Queue).setMessage(dead_message, key).send_delay(delay)
                        else:
                            message_record.status = MessageRecord.Status.FAILED
                        message_record.save()

                    time.sleep(1)


class RedisDelayConsumer(ABC):
    """
    暂未实现重试机制,也为对此类的子类进行注册
    实现重试机制后
    """

    def __init__(self):
        try:
            # 尝试获取 Redis 连接
            self._redis = get_redis_connection("default")
            # 测试连接
            self._redis.ping()
            self._redis_available = True
        except (ImportError, ConnectionError):
            # Redis 未安装或不可用
            self._redis_available = False

    def __init_subclass__(cls, **kwargs):
        """动态注册子类"""
        super().__init_subclass__(**kwargs)
        _register_consumer(cls)

    @property
    @abstractmethod
    def topic(self) -> str:
        return ''

    @abstractmethod
    def process_message(self, key: str, message, call_back=None):
        """
        开发者必须实现这个方法来处理消息
        """
        pass

    def consume(self):
        if not self._redis_available:
            return
        """
        消费消息队列
        """

        topic = self.topic + "_delay"
        while True:
            current_time = time.time()
            message = self._redis.zrangebyscore(topic, '-inf', current_time, start=0, num=1)
            if message:
                message_data = message[0]
                self._redis.zrem(topic, message)

                message_id = message_data.get("id", 0)
                key = message_data.get("key", None)
                message_body_ori = message_data.get("message_body", '')
                call_back = message_data.get("call_back", None)

                message_body = try_parse_json(message_body_ori)

                message_record = MessageRecord.objects.get(id=message_id)
                if message_record:
                    message_record.consume_attempts = message_record.consume_attempts + 1
                    message_record.consume_time = timezone.now()
                    message_record.consumer_ip = get_ipv4_to_int()
                try:
                    with transaction.atomic():
                        self.process_message(key, message_body, call_back)

                    if message_record:
                        message_record.status = MessageRecord.Status.SUCCESS
                        message_record.save()
                except Exception as e:
                    # 加入死信队列
                    if message_record:
                        message_record.status = MessageRecord.Status.RETRY
                        message_record.failure_reason = str(e)

                        if message_record.consume_attempts < 3:
                            delay = message_record.consume_attempts * 60
                            # 重试
                            message_data.update({"call_back": self.__name__})
                            dead_message = json.dumps(message_data)
                            RedisProducer().setTopic(Dead_Letter_Queue).setMessage(dead_message, key).send_delay(delay)
                        else:
                            message_record.status = MessageRecord.Status.FAILED
                        message_record.save()

                    time.sleep(1)


def try_parse_json(value):
    try:
        # 尝试解析 JSON 字符串
        parsed_value = json.loads(value)
        return parsed_value
    except (json.JSONDecodeError, TypeError):
        # 如果不是有效的 JSON 字符串，则返回原始值和False
        return value