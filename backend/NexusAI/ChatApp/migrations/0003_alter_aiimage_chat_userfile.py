# Generated by Django 5.0.7 on 2024-07-15 13:18

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ChatApp', '0002_rename_image_aiimage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aiimage',
            name='chat',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='images', to='ChatApp.chat'),
        ),
        migrations.CreateModel(
            name='UserFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(blank=True, null=True, upload_to='Frontend-uploads/')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='uploaded_file', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]