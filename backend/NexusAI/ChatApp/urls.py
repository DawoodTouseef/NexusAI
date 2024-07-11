from .views import  *
from django.urls import path
from rest_framework_simplejwt import views as jwt_views

urlpatterns=[
    path("task/",task,name="task"),
    path("results/",results,name="results"),
    path("chat/",chat,name="chat"),
    path("new_thread/",new_thread,name="new-thread"),
    path('thread_info/<str:id>/',thread_info,name="thread-info"),
    path('home/', HomeView.as_view(), name='home'),
    path('logout/', LogoutView.as_view(), name='logout'),
path('token/',jwt_views.TokenObtainPairView.as_view(),
          name ='token_obtain_pair'),
     path('token/refresh/',
          jwt_views.TokenRefreshView.as_view(),
          name ='token_refresh'),

]
#handler404="ChatApp.views.error_404"