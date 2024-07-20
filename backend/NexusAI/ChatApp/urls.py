from .views import  *
from django.urls import path
from rest_framework_simplejwt import views as jwt_views

urlpatterns=[
    path("chat/",Huggingpt.as_view(),name="chat"),
    path("new_thread/",NewThread.as_view(),name="new-thread"),
    path('thread_info/<str:id>/',Thread_info.as_view(),name="thread-info"),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/',jwt_views.TokenObtainPairView.as_view(),
          name ='token_obtain_pair'),
     path('token/refresh/',
          jwt_views.TokenRefreshView.as_view(),
          name ='token_refresh'),
    path("threads/",Threads.as_view(),name="threads"),
    path('serve/<str:file>/<str:file_name>/', SendImage.as_view(), name='serve-file'),
    path("signup/",SignUp.as_view(),name="sign-up"),
    path('user/<int:id>/', UserDetail.as_view(), name='user-detail'),
]
#handler404="ChatApp.views.error_404"