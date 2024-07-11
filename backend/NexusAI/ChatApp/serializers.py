from rest_framework import serializers
from .models import *
from rest_framework.authentication import authenticate

class Threadserializers(serializers.Serializer):
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

class ALL_Chat_serializers(serializers.Serializer):
    class Meta:
        model=Chat
        fields="__all__"