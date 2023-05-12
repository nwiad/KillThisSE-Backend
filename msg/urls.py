from django.urls import path, include
from rest_framework.routers import DefaultRouter
from msg.views import MsgViewSet

router = DefaultRouter()
router.register("", MsgViewSet, basename="msg")


urlpatterns = router.urls