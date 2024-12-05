from rest_framework import serializers

# 用于缓存生成的序列化器
serializer_cache = {}

def create_serializer_for_model(model_class, fields="__all__"):
    """
    动态生成一个基于指定模型的序列化器
    :param model_class: Django 模型类
    :param fields: 需要包含的字段，可以是列表或 '__all__'
    :return: 动态生成的 ModelSerializer 类
    """
    # 检查是否已为该模型创建过序列化器
    if model_class in serializer_cache:
        return serializer_cache[model_class]

    # 定义内部 Meta 类，并将 fields 参数动态传递到 Meta 中
    Meta = type("Meta", (), {"model": model_class, "fields": fields})

    # 动态创建序列化器类，将 Meta 作为属性
    serializer_class = type(
        f"{model_class.__name__}Serializer",  # 名称
        (serializers.ModelSerializer,),       # 继承自 ModelSerializer
        {"Meta": Meta}                        # 包含 Meta 类
    )

    # 将生成的序列化器类存储到缓存中
    serializer_cache[model_class] = serializer_class

    return serializer_class
