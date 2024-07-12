from rest_framework.decorators import api_view
from django.http import JsonResponse
from Server.awesome_chat import *
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
from rest_framework.authentication import authenticate
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken


@ratelimit(key='ip', rate='100/m', method='POST', block=True)
@api_view(["POST"])
def task(request):
    data = request.data
    messages = data["messages"]
    response = task_planning(messages)
    return JsonResponse({"task":response})

@ratelimit(key='ip', rate='100/m', method='POST', block=True)
@api_view(['POST'])
def results(request):
    data = request.data
    messages = data["messages"]
    response = chat_huggingface(messages, return_results=True)
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

@api_view(['POST'])
def threads(request):
    user=User.objects.filer(pk=request.data['user'])
    thread=Thread.objects.filter(created_by=request.user).all()
    try:
        thread_serializers=Threadserializers(thread,many=True)
    except Exception as e:
        thread_serializers=Threadserializers(thread,many=False)
    return JsonResponse(thread_serializers)

class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        print(request.user)
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
        user=User.objects.filter(pk=username)
        if user:
            user=authenticate(request,user)
            if user:

                user_serializers=Userserializers(user,many=True)
                return JsonResponse(user_serializers)

class Huggingpt(APIView):
    permission_classes = (IsAuthenticated,)
    #@ratelimit(key='ip', rate='100/m', method='GET', block=True)
    def post(self,request,*args,**kwargs):
        data = request.data
        messages = data["messages"]
        response = chat_huggingface(messages, return_planning=False, return_results=False)
        return JsonResponse(response)

class Threads(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self,request,*args,**kwargs):
        thread=Thread.objects.filter(created_by=request.user)
        thread_serializers=Threadserializers(thread,many=True)
        return JsonResponse(thread_serializers.data,safe=False)