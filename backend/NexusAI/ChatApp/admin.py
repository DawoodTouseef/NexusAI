from django.contrib import admin
from .models import *


admin.site.site_header="NexusAI DataBase"
admin.site.site_title="Nexus AI"
admin.site.register(User)
admin.site.register(Thread)
admin.site.register(Chat)
admin.site.register(Image)
admin.site.register(Audio)
admin.site.register(EmbeddingJson)
admin.site.register(Url)
admin.site.register(AIResponse)