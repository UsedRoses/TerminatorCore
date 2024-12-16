from django.db.models import Model
from django.http import JsonResponse
from TerminatorBaseCore.common.error_code import SUCCESS_CODE
from TerminatorBaseCore.utils.serializer_util import create_serializer_for_model


class ServiceJsonResponse(JsonResponse):

    def __init__(self, code: int = SUCCESS_CODE, message: str = "success", data=None):
        if isinstance(data, Model):
            serializer = create_serializer_for_model(data.__class__)
            data = serializer(data).data
        super(ServiceJsonResponse, self).__init__({'code': code, 'message': message, 'data': data})
