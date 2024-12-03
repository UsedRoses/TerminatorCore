import os
import importlib
from django.urls import path
from TerminatorBaseCore.route.viewset import CustomRouterViewSet


def load_custom_viewsets_from_directory(directory):
    """
    动态加载指定目录下继承自 CustomRouterViewSet 的所有 ViewSet。
    """
    routes = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py') and file != '__init__.py':  # 只加载.py文件，排除__init__.py
                # 获取相对路径，并将其转换为模块路径
                relative_path = os.path.relpath(os.path.join(root, file), directory)
                module_path = os.path.splitext(relative_path)[0]  # 去掉.py扩展名
                module_path = module_path.replace(os.sep, '.')  # 将路径中的分隔符替换为点号
                module_path = f'{directory.replace("/", ".")}.{module_path}'

                try:
                    print(f"Loading module: {module_path}")  # 输出加载的模块名
                    module = importlib.import_module(module_path)

                    # 遍历模块中的所有属性
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        # 检查属性是否为类，并且是否继承自 CustomRouterViewSet
                        if (isinstance(attr, type)
                                and issubclass(attr, CustomRouterViewSet)
                                and attr is not CustomRouterViewSet):
                            # 将 ViewSet 的路由添加到 routes 中
                            routes.extend(attr.get_routes())
                except ImportError as e:
                    print(f"Error importing {module_path}: {e}")
                except Exception as e:
                    print(f"Error loading {module_path}: {e}")

    return routes
