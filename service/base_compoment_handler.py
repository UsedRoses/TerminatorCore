from abc import abstractmethod
from typing import Optional, TypeVar, Generic, get_args

from django.core.exceptions import FieldError
from django.db.models import Model, Q
from rest_framework import status, serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from TerminatorBaseCore.common.error_code import ERROR_CODE, SUCCESS_MSG, SUCCESS_CODE
from TerminatorBaseCore.route.route import route, Method

T = TypeVar('T', bound=Model)


class BaseCompomentHandler(Generic[T]):
    """
    一个通用的 ViewSet，包含增删改查的基础方法。
    继承此类的子类需指定 `model`。
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(BaseCompomentHandler, cls).__new__(cls)
            for item in cls._instance.__orig_bases__:
                if item.__name__ == 'BaseCompomentHandler':
                    cls._instance.model = get_args(item)[0]
        return cls._instance

    @property
    def key_field_name(self) -> str:
        return 'pk'

    @property
    def delete_field(self) -> str:
        return 'is_deleted'

    @property
    def queryset(self):
        """基于传入的 model 获取查询集"""
        if self.model is None:
            raise ValueError("`model` attribute must be defined.")
        queryset = self.model.objects.all()
        if hasattr(self.model, self.delete_field):
            queryset = queryset.filter(**{self.delete_field: False})
        return queryset

    @property
    def serializer_class(self):
        """动态生成序列化器类"""
        if self.model is None:
            raise ValueError("`model` attribute must be defined.")

        class DynamicModelSerializer(serializers.ModelSerializer):
            class Meta:
                model = self.model
                fields = '__all__'

        return DynamicModelSerializer

    def get_object(self, lookup_value):
        """根据自定义主键字段获取对象实例，支持逻辑删除检查"""
        filter_kwargs = {self.key_field_name: lookup_value}
        if hasattr(self.model, self.delete_field):
            filter_kwargs[self.delete_field] = False
        try:
            return self.queryset.get(**filter_kwargs)
        except self.model.DoesNotExist:
            return None

    @route("retrieve", methods=[Method.GET])
    def retrieve(self, request):
        """获取单个对象详情"""
        obj = self.get_object(request.query_params.get(self.key_field_name))
        if obj is None:
            return Response({'code': ERROR_CODE, 'message': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(obj)
        return Response(serializer.data)

    @route("create", methods=[Method.POST])
    def create(self, request):
        """创建对象"""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'code': ERROR_CODE, 'message': SUCCESS_MSG, 'data': serializer.data}, status=status.HTTP_201_CREATED)

    @route("update", methods=[Method.POST])
    def update(self, request):
        """更新对象"""
        obj = self.get_object(request.data.get(self.key_field_name))
        if obj is None:
            return Response({'code': ERROR_CODE, 'message': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'code': ERROR_CODE, 'message': SUCCESS_MSG, 'data': serializer.data}, status=status.HTTP_200_OK)

    @route("remove", methods=[Method.POST])
    def soft_delete(self, request):
        """逻辑删除对象（仅当模型具有逻辑删除字段时有效）"""
        obj = self.get_object(request.data.get(self.key_field_name))
        if obj is None:
            return Response({'code': ERROR_CODE, 'message': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        if hasattr(obj, self.delete_field):
            setattr(obj, self.delete_field, True)
            obj.save()
            return Response({'code': SUCCESS_CODE, 'message': 'Object soft deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'code': ERROR_CODE, 'message': 'Logical delete not supported on this model.'},
                            status=status.HTTP_400_BAD_REQUEST)

    @route("delete", methods=[Method.POST])
    def destroy(self, request):
        """硬删除对象"""
        obj = self.get_object(request.data.get(self.key_field_name))
        if obj is None:
            return Response({'code': ERROR_CODE, 'message': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        obj.delete()
        return Response({'code': SUCCESS_CODE, 'message': SUCCESS_MSG}, status=status.HTTP_204_NO_CONTENT)

    @route("search", methods=[Method.POST])
    def search(self, request):
        """根据传入条件执行复杂查询"""
        queryset = self.queryset
        conditions = request.data

        filters = Q()
        model_fields = [field.name for field in self.queryset.model._meta.get_fields()]

        for field, value in conditions.items():
            # 拆分字段和条件运算符，例如 price:gt -> price 和 gt
            if ':' in field:
                field_name, operator = field.split(':', 1)
            else:
                field_name, operator = field, 'exact'

            # 检查字段是否在模型中存在
            if field_name not in model_fields:
                continue  # 忽略不存在的字段

            try:
                if operator == 'in':
                    filters &= Q(**{f"{field_name}__in": value.split(',')})
                elif operator == 'gt':
                    filters &= Q(**{f"{field_name}__gt": value})
                elif operator == 'lt':
                    filters &= Q(**{f"{field_name}__lt": value})
                elif operator == 'gte':
                    filters &= Q(**{f"{field_name}__gte": value})
                elif operator == 'lte':
                    filters &= Q(**{f"{field_name}__lte": value})
                elif operator == 'like':
                    filters &= Q(**{f"{field_name}__icontains": value})
                else:
                    # 默认使用精确匹配
                    filters &= Q(**{field_name: value})
            except FieldError:
                return Response({'message': f'Invalid field: {field_name}'},
                                status=status.HTTP_400_BAD_REQUEST)

        queryset = queryset.filter(filters)

        # 初始化分页器
        paginator = PageNumberPagination()
        paginator.page_size_query_param = "page_size"
        paginated_queryset = paginator.paginate_queryset(queryset, request)

        # 序列化分页后的数据
        serializer = self.serializer_class(paginated_queryset, many=True)
        return Response({'code': SUCCESS_CODE, 'message': SUCCESS_MSG, 'data': {
            'count': paginator.page.paginator.count,
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'results': serializer.data,
        }}, status=status.HTTP_204_NO_CONTENT)
