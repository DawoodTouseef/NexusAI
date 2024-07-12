from .views import  *
from django.urls import path
from rest_framework_simplejwt import views as jwt_views

urlpatterns=[
    path("task/",task,name="task"),
    path("results/",results,name="results"),
    path("chat/",Huggingpt.as_view(),name="chat"),
    path("new_thread/",new_thread,name="new-thread"),
    path('thread_info/<str:id>/',thread_info,name="thread-info"),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/',jwt_views.TokenObtainPairView.as_view(),
          name ='token_obtain_pair'),
     path('token/refresh/',
          jwt_views.TokenRefreshView.as_view(),
          name ='token_refresh'),
    path("threads/",Threads.as_view(),name="threads")
]
#handler404="ChatApp.views.error_404"