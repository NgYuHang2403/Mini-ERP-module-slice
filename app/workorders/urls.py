from django.urls import path
from .views import home, activity_log

urlpatterns = [
    path("", home, name="home"),
    path("<int:wo_id>/activity/", activity_log, name="activity_log"),
]