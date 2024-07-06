from rest_framework.decorators import api_view
from django.http import JsonResponse
from Server.awesome_chat import chat_huggingface
from django_ratelimit.decorators import ratelimit
from .models import *
import os
import binascii
from .serializers import *

@ratelimit(key='ip', rate='100/m', method='POST', block=True)
@api_view(["POST"])
def task(request):
    data = request.data
    messages = data["messages"]
    response = chat_huggingface(messages,return_planning=True)
    return JsonResponse(response)

@ratelimit(key='ip', rate='100/m', method='POST', block=True)
@api_view(['POST'])
def results(request):
    data = request.data
    messages = list(data)
    response = chat_huggingface(messages, return_results=True)
    return JsonResponse(response)

@ratelimit(key='ip', rate='100/m', method='POST', block=True)
@api_view(["POST"])
def chat(requests):
    data=requests.data
    messages = data["messages"]
    response=chat_huggingface(messages)
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

