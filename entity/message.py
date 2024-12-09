from django.db import models
from django.db.models import Model


class MessageRecord(Model):
    class Status(models.TextChoices):
        QUEUED = 'queued', 'Queued'
        PROCESSING = 'processing', 'Processing'
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'
        RETRY = 'retry', 'Retry'

    id = models.AutoField(primary_key=True)
    topic = models.CharField(max_length=50, verbose_name="主题")
    key = models.CharField(max_length=50, verbose_name="业务记录")
    message_body = models.JSONField(verbose_name="Message Body")  # 消息体，使用 JSON 格式存储
    producer_ip = models.PositiveBigIntegerField(verbose_name="Producer IP")  # 生产者 IP，整数存储
    consumer_ip = models.PositiveBigIntegerField(verbose_name="Consumer IP", null=True, blank=True)  # 消费者 IP，可为空
    enqueue_time = models.DateTimeField(auto_now_add=True, verbose_name="Enqueue Time")  # 消息入队时间
    consume_time = models.DateTimeField(null=True, blank=True, verbose_name="Consume Time")  # 消费时间
    consume_attempts = models.PositiveIntegerField(default=0, verbose_name="Consume Attempts")  # 消费次数
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.QUEUED, verbose_name="Status"
    )  # 消费状态
    failure_reason = models.TextField(null=True, blank=True, verbose_name="Failure Reason")  # 失败原因

    class Meta:
        verbose_name = "Message Queue"
        verbose_name_plural = "Message Queues"
        db_table = "message_record"  # 数据库表名

    def __str__(self):
        return f"Message {self.id} ({self.get_status_display()})"

