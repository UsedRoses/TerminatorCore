from TerminatorBaseCore.common.constant import Dead_Letter_Queue
from TerminatorBaseCore.utils.redis_mq_util import RedisDelayConsumer


class DeadConsumer(RedisDelayConsumer):
    @property
    def topic(self) -> str:
        return Dead_Letter_Queue

    def process_message(self, key: str, message):
        print(key)
        print(message)