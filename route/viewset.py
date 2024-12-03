from rest_framework.viewsets import ViewSet
from django.urls import path
import importlib


class CustomRouterViewSet(ViewSet):
    @classmethod
    def get_routes(cls):
        """
        生成被 route 装饰器标记的方法对应的路由。
        """
        routes = []

        prefix = getattr(cls, 'route_prefix', '')  # 获取类的前缀，默认为空字符串
        permission_path = getattr(cls, 'permission_path', None)  # 获取权限类
        permission_cls = None
        if permission_path:
            try:
                module_path, class_name = permission_path.rsplit('.', 1)
                # 动态导入模块
                module = importlib.import_module(module_path)
                # 获取类
                permission_cls = getattr(module, class_name)
            except (ImportError, AttributeError) as e:
                print("routes permission_path error")
                permission_cls = None

        for attr_name in dir(cls):
            method = getattr(cls, attr_name)
            if hasattr(method, 'route_url_pattern'):
                url_pattern = f'{prefix}/{method.route_url_pattern}'.lstrip('/')  # 拼接前缀和路径
                methods = method.route_methods

                if permission_cls:
                    cls.permission_classes = [permission_cls]
                routes.append(
                    path(
                        url_pattern,
                        cls.as_view({methods[0]: attr_name}),
                        name=attr_name  # 确保名称是字符串
                    )
                )
        return routes
