from django.urls import path, include
import user.views as views

urlpatterns = [
    path('startup', views.startup),
    path('user_register', views.user_register),
    path('user_list', views.users)
]