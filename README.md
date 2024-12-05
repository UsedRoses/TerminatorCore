# TerminatorCore
Django的增强代码，不用手动添加路由，自带crud，代码生成器，简单的权限管理类，帮助缩减开发时间
仅限Django框架

# 1. 创建Django项目
# 2. ```pip install TerminatorCore```
# 3. 配置
- ### 在settings.py中引入TerminatorBaseCore
```python
INSTALLED_APPS = [
    'TerminatorBaseCore',
]
```
- ### 在urls.py中加入配置
load_custom_viewsets_from_directory方法directory参数为需要对外暴露的文件路径

'my_project/expose'意思为扫描该路径下的所有文件

```python
from TerminatorBaseCore.route.load_custom_viewsets_from_directory import load_custom_viewsets_from_directory

urlpatterns = [
    *load_custom_viewsets_from_directory('my_project/expose'),
]
```

- ### 使用基础代码生成器
```python
from TerminatorBaseCore.utils.entity_export_util import generate_model_code

if __name__ == '__main__':
    generate_model_code('uploadfile_image', 'my_project', 'localhost', 'root', 'root', 'test_demo')
```
这里generate_model_code有以下参数  
table_name  数据库表名  
project_name  项目名称  
host  数据库地址  
user  数据库账号  
password  数据库密码  
database  数据库

**生成器会在**___系统文档___**中生成model,expose,service文件,然后将文件复制到项目对应目录下即可**

# 功能一
settings.py中加入,即可开启接口权限校验
```python
PERMISSION_PATH = 'TerminatorBaseCore.service.authenticated_with_redis.AuthenticatedWithRedis'
```

```python
from TerminatorBaseCore.utils.token_manger import TokenManager

# 通过TokenManager实现token的生成校验
# 用户登录成功后为其生成一个token
def user_login(request):
    user_id = 1
    email = "11"
    token = TokenManager().generate_token(user_id, email)
    
    # 为request赋予一个new_token属性,在返回结果后如果有这个属性会自动在响应头X-Token加入token,前端监听响应头中X-Token属性,有值则更新本地token
    request.new_token = token

    # token随请求头的Authorization传递
```