from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # Inherit from Django's built-in user model which includes fields like username, email, password, etc.
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    
    bio = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)

    def __str__(self):
        return self.username

class Thread(models.Model):
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, related_name='threads', on_delete=models.CASCADE)

    def __str__(self):
        return self.title

class Chat(models.Model):
    thread = models.ForeignKey(Thread, related_name='chats', on_delete=models.CASCADE)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Chat by {self.sender.username} in {self.thread.title}'

class Response(models.Model):
    chat = models.ForeignKey(Chat, related_name='responses', on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Response for chat {self.chat.id}'

class Image(models.Model):
    chat = models.ForeignKey(Chat, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='chat_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Image for chat {self.chat.id}'

class Audio(models.Model):
    chat = models.ForeignKey(Chat, related_name='audios', on_delete=models.CASCADE)
    audio = models.FileField(upload_to='chat_audios/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Audio for chat {self.chat.id}'

class Url(models.Model):
    chat = models.ForeignKey(Chat, related_name='urls', on_delete=models.CASCADE)
    url = models.URLField()
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.url

class EmbeddingJson(models.Model):
    chat = models.ForeignKey(Chat, related_name='embedding_jsons', on_delete=models.CASCADE)
    embedding = models.JSONField()
    X = models.IntegerField()
    Y = models.IntegerField()
    Z = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Embedding for chat {self.chat.id}'
