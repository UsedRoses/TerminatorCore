from aliyun.log import UwsgiQueuedLogHandler
import logging

from TerminatorBaseCore.components.aliyun_util import get_access_key


class DynamicUwsgiQueuedLogHandler(UwsgiQueuedLogHandler):
    def __init__(self, get_credentials_func, endpoint, project, logstore, *args, **kwargs):
        """
        :param get_credentials_func: 用于动态获取密钥的函数
        :param endpoint: 阿里云日志服务的终端节点
        :param logstore: 日志存储的名称
        """
        self.get_credentials_func = get_credentials_func

        # 初次获取密钥
        credentials = get_credentials_func()
        required_params = ['access_key_id', 'access_key']
        for param in required_params:
            if param not in credentials:
                raise ValueError(f"Missing required credential parameter: {param}")

        # 更新 kwargs，并包含 endpoint 和 logstore
        kwargs.update({
            'access_key_id': credentials['access_key_id'],
            'access_key': credentials['access_key'],
            'end_point': endpoint,
            'project': project,
            'log_store': logstore,
            'extract_json': True,
            'extract_json_drop_message': True
        })

        super().__init__(*args, **kwargs)

    def emit(self, record):
        """
        在每次 emit 时检查并动态更新密钥。
        """
        new_credentials = self.get_credentials_func()
        if new_credentials['access_key_id'] != self.access_key_id or new_credentials['access_key'] != self.access_key:
            # 动态更新密钥
            self.access_key_id = new_credentials['access_key_id']
            self.access_key = new_credentials['access_key']
        super().emit(record)


# 获取动态 Access Key 和 Access Key ID
def get_aliyun_log_access():
    access_key_id, access_key = get_access_key()
    return {
        'access_key_id': access_key_id,
        'access_key': access_key,
    }

def get_request_real_ip(request):
    cf_real_ip = request.META.get("HTTP_X_ORIGINAL_FORWARDED_FOR", "")
    ip = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if not ip:
        ip = request.META.get('REMOTE_ADDR', "")
    if cf_real_ip != "":
        client_ip = cf_real_ip
    else:
        client_ip = ip.split(",")[-1].strip() if ip else ""
    return client_ip


api_log = logging.getLogger('api_log')
