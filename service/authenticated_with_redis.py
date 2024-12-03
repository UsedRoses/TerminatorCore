from rest_framework.permissions import BasePermission
from django_redis import get_redis_connection

from TerminatorBaseCore.entity.design_patterns import Singleton
from TerminatorBaseCore.utils.token_manger import TokenManager


class AuthenticatedWithRedis(BasePermission, Singleton):
    """
    使用 Redis 检查 token 是否有效的自定义权限类。如果 Redis 未安装或不可用，则权限验证自动失效。
    """
    _init = False

    def __init__(self):
        if not AuthenticatedWithRedis._init:
            try:
                # 尝试获取 Redis 连接
                self.redis_client = get_redis_connection("default")
                # 测试连接
                self.redis_client.ping()
                self.redis_available = True
                if self.redis_available:
                    self.token_manager = TokenManager()
            except (ImportError, ConnectionError):
                # Redis 未安装或不可用
                self.redis_available = False
            AuthenticatedWithRedis._init = True

    def has_permission(self, request, view):
        # 如果 Redis 不可用，直接返回 True，跳过权限检查
        if not self.redis_available:
            return True

        token = request.headers.get("Authorization")

        if not token:
            return False

        res, user_id, email, new_token = self.token_manager.verify_token(token)

        if not res:
            return False  # Token 无效

        # 将 user_id 和新 token 注入到请求对象中，供后续逻辑使用
        request.user_id = user_id
        request.email = email
        request.new_token = new_token  # 如果生成了新 token，则在此保存

        return True

