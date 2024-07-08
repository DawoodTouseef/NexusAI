from rest_framework.decorators import api_view
from django.http import JsonResponse
from Server.awesome_chat import chat_huggingface
from django_ratelimit.decorators import ratelimit
import os
import binascii
from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from .models import *
from rest_framework.exceptions import AuthenticationFailed
from django.shortcuts import render

@ratelimit(key='ip', rate='100/m', method='POST', block=True)
@api_view(["POST"])
def task(request):
    data = request.data
    messages = data["messages"]
    response = chat_huggingface(messages,return_planning=True)
    return JsonResponse({"task":response})

@ratelimit(key='ip', rate='100/m', method='POST', block=True)
@api_view(['POST'])
def results(request):
    data = request.data
    messages = data["messages"]
    response = chat_huggingface(messages, return_results=True)
    return JsonResponse(response)

@ratelimit(key='ip', rate='100/m', method='POST', block=True)
@api_view(["POST"])
def chat(requests):
    data=requests.data
    messages = data["messages"]
    response=chat_huggingface(messages,return_planning=False, return_results=False)
    return JsonResponse(response)

@api_view(['POST'])
def new_thread(request):
    token=binascii.hexlify(os.urandom(20)).decode()
    thread=Thread(created_by=request.user,title=request.data['title'],title_id=token)
    thread.save()
    try:
        thread_serializers=Threadserializers(thread,many=True)
    except Exception as e:
        thread_serializers=Threadserializers(thread,many=False)
    return JsonResponse(thread_serializers)

@api_view(['POST'])
def thread_info(request,id):
    thread=Thread.objects.filter(created_by=request.user,title_id=id).all()
    try:
        thread_serializers=Threadserializers(thread,many=True)
    except Exception as e:
        thread_serializers=Threadserializers(thread,many=False)
    return JsonResponse(thread_serializers)


class HomeView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        content = {'message': request.data.get('username')}
        return Response(content)

class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):

        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class Login(APIView):
    def post(self,request):
        username=request.data.get("username")
        email=request.data.get('email')
        password=request.data.get("password")
        if email:
            user_obj=User.objects.filter(email=email).first()
        else:
            user_obj=User.objects.filter(username=username).first()
        if user_obj is None:
            return AuthenticationFailed("User not found")


        if not user_obj.check_password(raw_password=password):
            raise AuthenticationFailed("Incorrect Password or Email")

def error_404(request,exception):
    print(exception)
    return render(request,"exception.html")
