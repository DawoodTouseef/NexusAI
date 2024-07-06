from .views import  *
from django.urls import path

urlpatterns=[
    path("task/",task,name="task"),
    path("results/",results,name="results"),
    path("chat/",chat,name="chat"),
    path("new_thread/",new_thread,name="new-thread"),
    path('thread_info/<str:id>/',thread_info,name="thread-info"),

]