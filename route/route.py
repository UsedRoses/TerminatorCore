import inspect
from functools import wraps
from typing import Optional

from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import JSONParser
from rest_framework.request import Request


class Method:
    GET = 'get'
    POST = 'post'
    PUT = 'put'
    PATCH = 'patch'
    DELETE = 'delete'
    HEAD = 'head'
    OPTIONS = 'options'
    TRACE = 'trace'

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


def route(url_pattern: str, methods: [str]=None):
    """
    自定义路由装饰器，用于 ViewSet 中的视图方法自动注册路由。

    :param url_pattern: 路由的 URL 模式
    :param methods: 允许的请求方法，如 ['get', 'post']
    """

    if methods is None:
        methods = [Method.GET]

    def decorator(func):
        # 将装饰器定义的信息保存在函数属性中
        func.route_url_pattern = url_pattern
        func.route_methods = methods

        @wraps(func)
        def wrapped_view(cls, request: Request, *args, **kwargs):
            """
            🌟 自动解析参数并传递给视图方法
            """
            # 合并请求参数：优先顺序：query string、form-data、JSON Body
            query_data = request.GET.dict() if hasattr(request, "GET") else {}
            form_data = request.POST.dict() if hasattr(request, "POST") else {}
            json_data = {}
            if request.content_type and "application/json" in request.content_type:
                json_data = request.data
            # 合并后，后面的同名参数会覆盖前面的
            combined_data = {**query_data, **form_data, **json_data}

            # 根据视图函数的签名，构造参数绑定字典
            sig = inspect.signature(func)
            bound_args = {}
            for name, param in sig.parameters.items():
                # 忽略 self 和 request
                if name in ("self", "request"):
                    continue

                # 如果参数已经在 URL kwargs 中，则直接使用
                if name in kwargs:
                    bound_args[name] = kwargs[name]
                    continue

                # 针对带有类型注解的情况
                if param.annotation != inspect.Parameter.empty:
                    target_type = param.annotation
                    # 如果是 DRF Serializer 子类，则将整个请求数据传递进去（除非请求中存在与参数同名的 dict）
                    if isinstance(target_type, type) and issubclass(target_type, serializers.Serializer):
                        if name in combined_data and isinstance(combined_data[name], dict):
                            data_for_serializer = combined_data[name]
                        else:
                            data_for_serializer = combined_data
                        serializer = target_type(data=data_for_serializer)
                        if serializer.is_valid():
                            bound_args[name] = serializer.validated_data
                        else:
                            raise ValidationError({name: serializer.errors})
                        continue

                    # 如果是基本类型，如 int, str, float 等，尝试从 combined_data 中获取对应的值
                    if name in combined_data:
                        raw_value = combined_data[name]
                        try:
                            bound_args[name] = target_type(raw_value)
                        except Exception:
                            raise ValidationError({name: f"Invalid value for {target_type.__name__}: {raw_value}"})
                        continue

                # 如果没有类型注解，则直接从 combined_data 中获取（字符串形式）
                if name in combined_data:
                    bound_args[name] = combined_data[name]
                else:
                    # 检查是否有默认值
                    if param.default != inspect.Parameter.empty:
                        bound_args[name] = param.default
                    else:
                        raise ValidationError({name: "This parameter is required."})

            # 调用原始视图函数，并传入解析后的参数
            return func(cls, request, *args, **bound_args)

        return wrapped_view

    return decorator
