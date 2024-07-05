from rest_framework.decorators import api_view
from django.http import JsonResponse
from Server.awesome_chat import chat_huggingface
from django_ratelimit.decorators import ratelimit

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