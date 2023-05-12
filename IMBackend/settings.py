"""
Django settings for IMBackend project.

Generated by 'django-admin startproject' using Django 4.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-zsd1(jud4^7u1-^^vzb8@o1=^@_q55(owv0jip$_0&2u$cwc#3'

# SECURITY WARNING: don't run with debug turned on in production!
# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

if os.getenv('DEPLOY'):
    DEBUG = False
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',  # 默认
            'NAME': 'im',  # 连接的数据库
            'HOST': 'database.KillThisSE.secoder.local',  # mysql的ip地址
            'PORT': 3306,  # mysql的端口
            'USER': 'root',  # mysql的用户名
            'PASSWORD': '123456',  # mysql的密码
            'OPTIONS': {
                'charset': 'utf8mb4'
            }
        }
    }
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": ["redis://redis.KillThisSE.secoder.local:6379"],
            },
        },
    }
else:
    DEBUG = True
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": ["redis://localhost:6379"],
            },
        },
    }

ALLOWED_HOSTS = [
    '*'
]


# Application definition

INSTALLED_APPS = [
    'daphne',
    'user',
    'msg',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'channels'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'IMBackend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'IMBackend.wsgi.application'

ASGI_APPLICATION = 'IMBackend.asgi.application'

AUTH_USER_MODEL = 'user.User'

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Password encryption
# https://docs.djangoproject.com/zh-hans/4.1/topics/auth/passwords/

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.ScryptPasswordHasher',
]


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


REST_FRAMEWORK = {
    'APPEND_SLASH' : False
}

APPEND_SLASH = False


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.163.com'  # SMTP服务器地址
EMAIL_PORT = 25
#发送邮件的邮箱
EMAIL_HOST_USER = '15935695163@163.com'
#在邮箱中设置的客户端授权密码
EMAIL_HOST_PASSWORD = 'ESWSOKLOMQGYQLDQ'
#收件人看到的发件人
EMAIL_FROM = '杀软团队<15935695163@163.com>'
