from typing import Optional

from django.conf import settings

# 用于保存所有动态添加的 URL 路由
route_patterns = []


def prefix(url_prefix: str, permission_path: Optional[str] = None):
    permission_path = getattr(settings, 'PERMISSION_PATH', None) if permission_path is None else permission_path
    """
    类装饰器，用于为 ViewSet 类添加统一的 URL 前缀。
    """
    def decorator(cls):
        cls.route_prefix = url_prefix  # 将前缀存储在类属性上
        cls.permission_path = permission_path
        return cls
    return decorator


def route(url_pattern: str, methods=['get']):
    """
    自定义路由装饰器，用于 ViewSet 中的视图方法自动注册路由。

    :param url_pattern: 路由的 URL 模式
    :param methods: 允许的请求方法，如 ['get', 'post']
    """

    def decorator(func):
        # 将装饰器定义的信息保存在函数属性中
        func.route_url_pattern = url_pattern
        func.route_methods = methods
        return func

    return decorator




