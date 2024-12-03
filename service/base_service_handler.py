from typing import TypeVar, Generic, get_args

from django.core.exceptions import FieldError
from django.db.models import Model, Q
from rest_framework import serializers

from TerminatorBaseCore.common.error_code import DELETE_ERROR_CODE
from TerminatorBaseCore.entity.exception import ServiceException

T = TypeVar('T', bound=Model)


class BaseServiceHandler(Generic[T]):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(BaseServiceHandler, cls).__new__(cls)
            for item in cls._instance.__orig_bases__:
                if item.__name__ == 'BaseServiceHandler':
                    cls._instance.model = get_args(item)[0]
        return cls._instance

    @property
    def _key_field_name(self) -> str:
        return 'id'

    @property
    def _delete_field(self) -> str:
        return 'is_deleted'

    @property
    def _queryset(self):
        """基于传入的 _model 获取查询集"""
        if self.model is None:
            raise ValueError("`_model` attribute must be defined.")
        queryset = self.model.objects.all()
        if hasattr(self.model, self._delete_field):
            queryset = queryset.filter(**{self._delete_field: False})
        return queryset

    @property
    def _serializer_class(self):
        """动态生成序列化器类"""
        if self.model is None:
            raise ValueError("`_model` attribute must be defined.")

        class Dynamic_modelSerializer(serializers.ModelSerializer):
            class Meta:
                model = self.model
                fields = '__all__'

        return Dynamic_modelSerializer

    def get(self, key_value, key_name=None) -> T | None:
        """根据自定义主键字段获取对象实例，支持逻辑删除检查"""
        if key_name:
            filter_kwargs = {key_name: key_value}
        else:
            filter_kwargs = {self._key_field_name: key_value}
        if hasattr(self.model, self._delete_field):
            filter_kwargs[self._delete_field] = False
        try:
            return self._queryset.get(**filter_kwargs)
        except self.model.DoesNotExist:
            return None

    def create(self, data: dict):
        """创建对象"""
        serializer = self._serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return serializer.data

    def update(self, data: dict) -> T | None:
        """更新对象"""
        obj = self.get(key_value=data.get(self._key_field_name))
        if obj is None:
            return None

        serializer = self._serializer_class(obj, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        obj.refresh_from_db()
        return obj

    def soft_delete(self, key_value):
        """逻辑删除对象（仅当模型具有逻辑删除字段时有效）"""
        obj = self.get(key_value=key_value)
        if obj is None:
            return None

        if hasattr(obj, self._delete_field):
            setattr(obj, self._delete_field, True)
            obj.save()
            return None
        else:
            raise ServiceException(message='Logical delete not supported on this _model.', code=DELETE_ERROR_CODE)

    def destroy(self, key_value):
        """硬删除对象"""
        obj = self.get(key_value=key_value)
        if obj is None:
            return None

        obj.delete()
        return None

    def select(self, params: dict) -> list[T]:
        """根据传入条件执行复杂查询"""
        _queryset = self._queryset

        filters = Q()
        _model_fields = [field.name for field in self._queryset._model._meta.get_fields()]

        for field, value in params.items():
            if field not in _model_fields:
                continue  # 忽略不存在的字段

            try:
                if field.endswith('__in'):
                    filters &= Q(**{field: value.split(',')})
                elif field.endswith('__gt'):
                    filters &= Q(**{field: value})
                elif field.endswith('__gte'):
                    filters &= Q(**{field: value})
                elif field.endswith('__lt'):
                    filters &= Q(**{field: value})
                elif field.endswith('__lte'):
                    filters &= Q(**{field: value})
                elif field.endswith('__icontains'):
                    filters &= Q(**{field: value})
                else:
                    filters &= Q(**{field: value})
            except FieldError:
                pass

        return _queryset.filter(filters)