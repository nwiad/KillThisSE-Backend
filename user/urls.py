from django.urls import path, include
import user.views as views

urlpatterns = [
    path('startup', views.startup),
    path('user_register', views.user_register),
    path('user_login', views.user_login),
    path('user_logout', views.user_logout),
    path('users', views.users)
]