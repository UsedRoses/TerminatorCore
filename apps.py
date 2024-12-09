from django.apps import AppConfig
from django.conf import settings
import logging
import importlib
import inspect
from TerminatorBaseCore.utils.redis_mq_util import RedisConsumer


class TerminatorBaseCoreConfig(AppConfig):
    name = 'TerminatorBaseCore'

    def ready(self):
        logging.info("TerminatorBaseCoreConfig ready() has been triggered.")

        # 确保INSTALLED_APPS列表已经存在
        if not hasattr(settings, 'INSTALLED_APPS'):
            settings.INSTALLED_APPS = []

        if 'corsheaders' not in settings.INSTALLED_APPS:
            settings.INSTALLED_APPS.append('corsheaders')

        if 'rest_framework' not in settings.INSTALLED_APPS:
            settings.INSTALLED_APPS.append('rest_framework')

        # 确保MIDDLEWARE列表已经存在
        if not hasattr(settings, 'MIDDLEWARE'):
            settings.MIDDLEWARE = []

        if 'corsheaders.middleware.CorsMiddleware' not in settings.MIDDLEWARE:
            settings.MIDDLEWARE.insert(0, 'corsheaders.middleware.CorsMiddleware')

        # 检查是否已经添加了中间件，避免重复添加
        if 'TerminatorBaseCore.middleware.token_middleware.TokenMiddleware' not in settings.MIDDLEWARE:
            settings.MIDDLEWARE.append('TerminatorBaseCore.middleware.token_middleware.TokenMiddleware')
        if 'TerminatorBaseCore.middleware.exception_middleware.ExceptionHandlingMiddleware' not in settings.MIDDLEWARE:
            settings.MIDDLEWARE.append('TerminatorBaseCore.middleware.exception_middleware.ExceptionHandlingMiddleware')

        # 暴露自定义响应头，允许前端访问这些头信息
        if not hasattr(settings, 'CORS_EXPOSE_HEADERS'):
            settings.CORS_EXPOSE_HEADERS = []

        settings.CORS_EXPOSE_HEADERS.append("X-Token")

        if not hasattr(settings, 'REST_FRAMEWORK'):
            settings.REST_FRAMEWORK = {
                'DEFAULT_RENDERER_CLASSES': (
                    'rest_framework.renderers.JSONRenderer',  # 只使用 JSON 渲染器
                ),
            }

def start_consumers():
    # 获取所有子类
    consumer_classes = []

    # 查找项目中的所有子类实现
    for app in settings.INSTALLED_APPS:
        if app.startswith("django"):
            continue
        if app == 'TerminatorBaseCore':
            continue

        # 动态导入应用中的模块
        try:
            module = importlib.import_module(f"{app}.consumers")
        except ModuleNotFoundError:
            continue

            # 查找所有继承自 RedisConsumer 的子类
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, RedisConsumer) and obj is not RedisConsumer:
                consumer_classes.append(obj)

        # 启动所有消费者
        for consumer_class in consumer_classes:
            consumer_instance = consumer_class()
            consumer_instance.consume()

    # 如果有消费者,则启动死信队列
    if consumer_classes:
        # 动态导入应用中的模块
        try:
            module = importlib.import_module("TerminatorBaseCore.consumers")
        except ModuleNotFoundError:
            return

        t_consumer_classes = []
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, RedisConsumer) and obj is not RedisConsumer:
                t_consumer_classes.append(obj)

        for consumer_class in t_consumer_classes:
            consumer_instance = consumer_class()
            consumer_instance.consume()
