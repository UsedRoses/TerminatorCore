import traceback
from django.utils.deprecation import MiddlewareMixin
from TerminatorBaseCore.common.error_code import ERROR_CODE, SUCCESS_CODE
from TerminatorBaseCore.components.dynamic_call import HandleRegister, BusinessExceptionAfterHandle, \
    ServiceExceptionAfterHandle, InfoExceptionAfterHandle, ExceptionAfterHandle
from TerminatorBaseCore.entity.exception import BusinessException, InfoException, ServiceException
from TerminatorBaseCore.entity.response import ServiceJsonResponse


class ExceptionHandlingMiddleware(MiddlewareMixin):

    def process_exception(self, request, exception):
        traceback.print_exc()
        if isinstance(exception, BusinessException):
            error_code = exception.code if exception.code else ERROR_CODE
            HandleRegister.instance_and_execute(BusinessExceptionAfterHandle.AfterHandleName, request,
                                                message=exception.message)
            return ServiceJsonResponse(error_code, exception.message)
        elif isinstance(exception, ServiceException):
            HandleRegister.instance_and_execute(ServiceExceptionAfterHandle.AfterHandleName, request,
                                                message=exception.message)
            return ServiceJsonResponse(ERROR_CODE, exception.message)
        elif isinstance(exception, InfoException):
            HandleRegister.instance_and_execute(InfoExceptionAfterHandle.AfterHandleName, request,
                                                message=exception.message)
            return ServiceJsonResponse(SUCCESS_CODE, exception.message)
        elif isinstance(exception, Exception):
            HandleRegister.instance_and_execute(ExceptionAfterHandle.AfterHandleName, request,
                                                message=str(exception))
            return ServiceJsonResponse(ERROR_CODE, str(exception))
