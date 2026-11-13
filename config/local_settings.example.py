import os

from django.core.files.storage import FileSystemStorage

from config.default import LOGGING


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN_MODE = "DEVELOP"
DEBUG = True
STANDALONE_MODE = True
ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = ["http://127.0.0.1:8004", "http://localhost:8004"]
LOGIN_REDIRECT_URL = "/"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("MYSQL_NAME", "bk_itsm"),
        "USER": os.getenv("MYSQL_USER", "root"),
        "PASSWORD": os.getenv("MYSQL_PASSWORD", ""),
        "HOST": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "PORT": os.getenv("MYSQL_PORT", "3306"),
        "TEST": {"CHARSET": "utf8", "COLLATION": "utf8_general_ci"},
    }
}

REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_MODE = "single"
REDIS_SERVICE_NAME = "mymaster"
REDIS_SENTINEL_PASSWORD = ""
REDIS = {
    "host": REDIS_HOST,
    "port": REDIS_PORT,
    "password": REDIS_PASSWORD,
    "service_name": REDIS_SERVICE_NAME,
    "mode": REDIS_MODE,
    "db": REDIS_DB,
}
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}",
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    },
    "db": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache",
    },
    "login_db": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "account_cache",
    },
    "dummy": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
    "locmem": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
}

BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/3"
STORE = FileSystemStorage(location=os.path.join(PROJECT_ROOT, "USERRES"))

BK_PAAS_HOST = "http://127.0.0.1:9"
BK_PAAS_INNER_HOST = "http://127.0.0.1:9"
BK_COMPONENT_API_URL = "http://127.0.0.1:9"
BK_API_URL_TMPL = "http://127.0.0.1:9/{api_name}/api"
BK_LOGIN_URL = "/login/"
FRONTEND_URL = "/"
SITE_URL = "/"
MEDIA_URL = "/media/"

USE_BKCHAT = False
CLOSE_NOTIFY = "close"
CLOSE_EVERY_DAY_TICKET_NOTIFY = True
IS_USE_INVITE_SMS = False
INIT_DEVOPS_TEMPLATE = False
BKAPP_CI_ENABLED = False
