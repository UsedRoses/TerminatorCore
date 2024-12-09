import random
import string
import os
import time

from django.conf import settings
from django_redis import get_redis_connection
import jwt
from jwt import PyJWTError, ExpiredSignatureError
from TerminatorBaseCore.entity.design_patterns import Singleton


class TokenManager(Singleton):

    def __init__(self):
        if not hasattr(self, 'redis_client'):
            self.redis_client = get_redis_connection("default")
            self.token_lifetime = 3 * 24 * 3600  # token 的有效期为 3 天
            self.max_token_lifetime = 20 * 24 * 3600  # 强制失效时间为 20 天
            self.last_check_interval = 3600  # 每小时检查一次
            self.secret_key = getattr(settings, 'TOKEN_SECRET_KEY', "18xn21fj23plg24zf")
            self.project_name = getattr(settings, 'PROJECT_NAME', "T800")
            self.algorithm = "HS256"

    def generate_token(self, user_id, email: str):
        """生成带有用户信息和最近验证时间的 JWT token"""
        issued_at = int(time.time())
        last_verified = issued_at

        identity_id = self._generate_short_identity_id()

        payload = {
            "user_id": user_id,
            "email": email,
            "identity_id": identity_id,
            "iat": issued_at,
            "last_verified": last_verified,  # 存储上次验证时间
        }
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

        # 在 Redis 中存储 token 创建时间，用于强制失效判断
        redis_key = self._get_redis_key(token, identity_id)
        self.redis_client.set(redis_key, issued_at, ex=self.token_lifetime)

        return token

    def _generate_short_identity_id(self, length=6):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

    def _get_redis_key(self, user_id, identity_id):
        """获取 Redis 缓存的键"""
        return f"{self.project_name}_user_token:{user_id}:{identity_id}"

    def decode_token(self, token):
        """解码 JWT token 并返回 payload（不验证过期）"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options={"verify_exp": False})
            return payload
        except PyJWTError:
            return None

    def verify_token(self, token):
        """
        验证 token 的有效性。
        - 超过一小时验证 Redis 并更新 last_verified。
        - 若已达20天强制失效时间，从 Redis 删除。
        """
        try:
            payload = self.decode_token(token)
            if not payload:
                return False, None, None, None

            user_id = payload.get("user_id")
            email = payload.get("email")
            identity_id = payload.get("identity_id")
            last_verified = payload.get("last_verified")
            current_time = int(time.time())
            # 如果距上次验证不到一小时，直接返回有效
            if current_time - last_verified < self.last_check_interval:
                return True, user_id, email, None

            redis_key = self._get_redis_key(token, identity_id)

            # 获取 Redis
            token_created = self.redis_client.get(redis_key)
            if token_created:
                # 检查是否超过20天
                token_created = int(token_created)

                # 检查是否超过强制失效时间
                if current_time - token_created > self.max_token_lifetime:
                    self.redis_client.delete(redis_key)
                    print("Token Forced failure")
                    return False, None, None, None
            else:
                # 不存在此Token
                print("Token Does not exist")
                return False, None, None, None

            # 更新 last_verified 时间并重置 token 的到期时间
            payload["last_verified"] = current_time

            # 使用新 payload 创建新的 token
            new_token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

            # 更新 Redis 过期时间
            self.redis_client.expire(redis_key, self.token_lifetime)

            return True, user_id, email, new_token

        except ExpiredSignatureError:
            print("Token Expired")
            return False, None, None, None
        except PyJWTError:
            print("Token JWTError")
            return False, None, None, None

    def invalidate_token(self, token, identity_id):
        """使 token 失效并删除 Redis 中的信息"""
        redis_key = self._get_redis_key(token, identity_id)
        self.redis_client.expire(redis_key, 2 * 60)
