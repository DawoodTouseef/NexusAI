from rest_framework import serializers
from .models import *
from rest_framework.authentication import authenticate

class Threadserializers(serializers.ModelSerializer):
    class Meta:
        model=Thread
        fields="__all__"


class Userserializers(serializers.Serializer):
    class Meta:
        model=User
        fields="__all__"


class UserRegister_serializers(serializers.Serializer):
    class Meta:
        model=User
        fields="__all__"

    def create(self, validated_data):
        user_obj=User.objects.create_user(username=validated_data.get("username"),email=validated_data.get("email"))
        user_obj.set_password(raw_password=validated_data.get("password"))
        user_obj.save()


class UserLogin_serializers(serializers.Serializer):
    class Meta:
        model=User
        fields="__all__"

    def check_user(self,validated_data):
        user=authenticate(username=validated_data.get("username"),password=validated_data.get("password"))
        if user:
            return user


class AIResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIResponse
        fields = ['message']

class ChatSerializer(serializers.ModelSerializer):
    responses = AIResponseSerializer(many=True, read_only=True)

    class Meta:
        model = Chat
        fields = ['message', 'responses']

class ImageSeializer(serializers.ModelSerializer):
    class Meta:
        model=AIImage
        fields=["image"]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username', 'email', 'bio', 'profile_image']


class ReactChatSerializer(serializers.Serializer):
    messages = serializers.ListField(
        child=serializers.JSONField()
    )
    file = serializers.FileField(required=False)
    threads = serializers.CharField(required=False)
