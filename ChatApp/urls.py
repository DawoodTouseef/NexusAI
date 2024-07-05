from .views import  *
from django.urls import path

urlpatterns=[
    path("task/",task,name="task"),
    path("results/",results,name="results"),
    path("chat/",chat,name="chat"),

]