from rest_framework import serializers
from .models import *

class Threadserializers(serializers.Serializer):
    class Meta:
        model=Thread
        fields="__all__"