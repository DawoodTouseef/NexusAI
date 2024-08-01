from Server.awesome_chat import *
import os
import binascii
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .models import *
from rest_framework.authentication import authenticate
from django.http import FileResponse
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from .models import User
from django.contrib.auth.hashers import make_password
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
import json
from pathlib import Path
from huggingface_hub import InferenceClient
from langchain.tools import Tool


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

class healthcheck(APIView):
    def post(self,request,*args,**kwargs):
        return JsonResponse({"message":True})
    def get(self,reuest,*args,**kwargs):
        return JsonResponse({"message": True})
class NewThread(APIView):
    permission_classes = (IsAuthenticated,)
    def post(self,request,*args,**kwargs):
        token = binascii.hexlify(os.urandom(20)).decode()
        thread = Thread(created_by=request.user, title=request.data['title'], title_id=token)
        thread.save()
        return JsonResponse({"title_id":token})

class Thread_info(APIView):
    permission_classes = (IsAuthenticated,)
    def post(self,request,id,*args,**kwargs):
        try:
            thread = Thread.objects.get(title_id=id,created_by=request.user)
        except Thread.DoesNotExist:
            return Response({"error": "Thread not found"}, status=404)

        chats = Chat.objects.filter(thread=thread)
        serialized_chats = ChatSerializer(chats, many=True)

        response_data = [
            {"user": chat["message"], "assistant": chat["responses"][0]["message"] if chat["responses"] else "",}
            for chat in serialized_chats.data
        ]
        i=0
        image_lists=[]
        for chat in chats:
            image=AIImage.objects.filter(chat=chat)
            image=ImageSeializer(image,many=True)
            image_list=list(image.data)
            image_lists.append(image_list)

        response=[]
        for i in range(len(response_data)):
            response.append({"user":response_data[i]['user'],"assistant":response_data[i]['assistant'],"id":i,"path":image_lists[i]})
        return JsonResponse({"response":response})


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

class Delete_thread(APIView):
    permission_classes = (IsAuthenticated)
    def post(self,request,*args,**kwargs):
        pass
class Login(APIView):
    def post(self,request):
        username=request.data.get("username")
        user=User.objects.filter(pk=username)
        if user:
            user=authenticate(request,user)
            if user:

                user_serializers=Userserializers(user,many=True)
                return JsonResponse(user_serializers)

class SendImage(APIView):
    #permission_classes = (IsAuthenticated,)
    def get(self,request,file,file_name,*args,**kwargs):
        file_path=os.path.join(BASE_DIR,file,file_name)
        return FileResponse(open(file_path, 'rb'), content_type='application/octet-stream')
    def post(self,request,file,file_name,*args,**kwargs):
        file_path=os.path.join(BASE_DIR,file,file_name)
        return FileResponse(open(file_path, 'rb'), content_type='application/octet-stream')

class Huggingpt(APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser,)
    #@ratelimit(key='ip', rate='100/m', method='GET', block=True)
    def post(self,request,*args,**kwargs):
        serializer = ReactChatSerializer(data=request.data)
        if serializer.is_valid():
            messages = json.loads(serializer.validated_data.get('messages')[0])
            file = serializer.validated_data.get('file')
            title = serializer.validated_data.get('threads')
            thread=Thread.objects.get(title_id=title)
            self.chat=Chat(thread=thread,message=messages[-1]["content"])
            self.chat.save()
            chats = Chat.objects.filter(thread=thread)
            serialized_chats = ChatSerializer(chats, many=True)
            if file:
                user_file=UserFile.objects.create(
                    chat=self.chat,
                    file=file
                )
                user_file.file.save(file.name,file,save=True)
                print("File Saved Successfully")
            response_data = [
                {"user": chat["message"], "assistant": chat["responses"][0]["message"] if chat["responses"] else "",  }
                for chat in serialized_chats.data
            ]
            response = []

            for i in range(len(response_data)):
                response.append({"role":"user","content": response_data[i]['user']})
                response.append({"role":"assistant","content": response_data[i]['assistant']})
            for data in messages:
                response.append(data)
            try:
                from Server.Agents.InputModel import HuggingGpt_Input as T
                AIresponses = chat_huggingface(response, return_planning=False, return_results=False,chat=self.chat,tool=[
                    Tool(
                        name="stabilityai/stable-diffusion-2-1",
                        description="A Tool To convert a text to image.",
                        func=self.text_tom_image,
                        args_schema=T
                    )
                ])
                if AIresponses['message'] is None or AIresponses['message']=="":
                    AIresponses={}
                    AIresponses['message']=chat_llama(response,max_tokens=1500,stop=[])
                    AIresponses['path']=""
            except Exception as e:
                AIresponses = {}
                AIresponses['message'] = chat_llama(response, max_tokens=1500, stop=[])
                AIresponses['path'] = ""
            if AIresponses['message'] is None:
                AIresponses = {}
                AIresponses['message'] = chat_llama(response, max_tokens=1500, stop=[])
                AIresponses['path'] = ""
            ai_response=AIResponse(chat=self.chat,message=AIresponses['message'])
            ai_response.save()
            return JsonResponse(AIresponses)
        else:
            print("Not Done")
            return JsonResponse({"message":None,"path":None})
    def text_tom_image(self,inputs):
        result={}
        paths={}
        inference=InferenceClient(model="stabilityai/stable-diffusion-2-1",token=os.getenv("LLAMA_TOKEN"))
        prompt = hub.pull("hardkothari/prompt-maker")
        llm = HuggingFaceEndpoint(huggingfacehub_api_token=os.getenv("LLAMA_TOKEN"), model_kwargs={
            "max_tokens": 4096,
            "add_to_git_credential": True
        },
                                  repo_id="mistralai/Mixtral-8x7B-Instruct-v0.1")
        runnable = prompt | llm
        inputs = runnable.invoke(
            {
                "lazy_prompt": inputs,
                "task": "text-to-image",

            }

        )
        img = inference.text_to_image(inputs)  # Assuming inference() returns a PIL Image object
        name = str(uuid.uuid4())[:4]
        if isinstance(img, Image.Image):
            # Ensure `path` is a dictionary
            print("Saving an image.")
            image_bytes = BytesIO()
            img.save(image_bytes, format='PNG')  # Save PIL Image to BytesIO

            # Ensure chat is a single Chat instance, not a QuerySet
            ai_image = AIImage(chat=self.chat)
            ai_image.image.save(f"{name}.png", ContentFile(image_bytes.getvalue()), save=True)
            result["generated_image"] = f"Path of the Image='http://{API_URL}/serve/chat_images/{name}.png'"
            paths['path'] = f'http://{API_URL}/serve/chat_images/{name}.png'

class Threads(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self,request,*args,**kwargs):
        thread=Thread.objects.filter(created_by=request.user)
        thread_serializers=Threadserializers(thread,many=True)
        return JsonResponse(thread_serializers.data,safe=False)



class SignUp(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        file = request.FILES.get("file")
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")
        bio = request.data.get("bio")

        if not username or not email or not password:
            return Response({"message": "Username, email, and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({"message": "Username already exists."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({"message": "Email already exists."}, status=status.HTTP_400_BAD_REQUEST)

        user = User(
            username=username,
            email=email,
            password=make_password(password),
            bio=bio,
            profile_image=file
        )

        try:
            user.save()
            return Response({"message": "User created successfully."}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class UserDetail(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request, id, *args, **kwargs):
        user = get_object_or_404(User, id=id)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)