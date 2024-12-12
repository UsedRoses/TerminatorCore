from TerminatorBaseCore.common.constant import Dead_Letter_Queue
from TerminatorBaseCore.utils.redis_mq_util import RedisDelayConsumer, RedisProducer


class DeadConsumer(RedisDelayConsumer):
    @property
    def topic(self) -> str:
        return Dead_Letter_Queue

    def process_message(self, key: str, message, call_back=None):
        if call_back:
            RedisProducer().setTopic(call_back).setMessage(message, key).send(delay)
