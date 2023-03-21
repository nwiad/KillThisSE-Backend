from django.urls import path

import auth.views as views

urlpatterns = [
    path('startup', views.startup),
]