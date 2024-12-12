from pathlib import Path
from django.apps import AppConfig
from django.conf import settings
import logging
import importlib
import inspect


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

        project_name = getattr(settings, "PROJECT_NAME", None)
        if project_name:
            from django.apps import apps
            from TerminatorBaseCore.components.import_scan import ImportScan
            scan = ImportScan()
            # 获取所有已注册的 app
            for app_config in apps.get_app_configs():
                if app_config.name == project_name:
                    app_path = Path(app_config.path)
                    scan.scan_modules(app_path, app_config.name)

