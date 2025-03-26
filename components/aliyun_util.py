from django.conf import settings


def get_access_key():
    file_ram_path = '/nas/zbase/security-credentials/ali_ram'

    access_key_id = settings.ACCESS_KEY_ID
    access_key_secret = settings.ACCESS_KEY_SECRET
    try:
        with open(file_ram_path, 'r') as f:
            content = f.read()
            access_key_id, access_key_secret = content.split('\n')[0:2]
    except Exception as e:
        access_key_id = "LTAI5tSBGyaBxbCmnBRPNKG9"
        access_key_secret = "PIc8HNGu8ANknf9MDnh8ifA3uV0P98"
    finally:
        return access_key_id, access_key_secret