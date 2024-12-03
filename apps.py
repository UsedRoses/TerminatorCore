from django.apps import AppConfig
from django.conf import settings
import logging


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



