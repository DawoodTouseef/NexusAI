from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
from .models import *
from Server.awesome_chat import chat_huggingface

@api_view(["POST"])
def task(request):
    user=request.user
    data = request.data
    messages = data["messages"]
    thread=Thread.objects.filter(created_by=user)
    chat=Chat(thread=thread,message=messages[:-1]['content'])
    chat.save()
    response = chat_huggingface(messages,return_planning=True)
    response = Response(chat=chat, message=response['message'])
    response.save()
    return JsonResponse(response)

@api_view(['POST'])
def results(request):
    user=request.user
    data = request.data
    messages = data["messages"]
    response = chat_huggingface(messages, return_results=True)
    messages = data["messages"]
    thread = Thread.objects.filter(created_by=user)
    chat = Chat(thread=thread, message=messages[:-1]['content'])
    response = Response(chat=chat, message=response['message'])
    response.save()
    chat.save()
    return JsonResponse(response)


@api_view(["POST"])
def chat(requests,thread_name):
    user=requests.user
    data=requests.data
    messages = data["messages"]
    response=chat_huggingface(messages)
    thread = Thread.objects.filter(created_by=user,title=thread_name)
    chat = Chat(thread=thread, message=messages[:-1]['content'])
    response = Response(chat=chat, message=response['message'])
    response.save()
    chat.save()
    return JsonResponse(response)