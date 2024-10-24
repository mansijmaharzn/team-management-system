import os
from pathlib import Path
from dotenv import load_dotenv

from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

from users.tasks import send_email_task

env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email")


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "email", "password")
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            validated_data["username"],
            validated_data["email"],
            validated_data["password"],
        )
        subject = "Thanks for creating account!"
        message = "We would expect you to view this email ;)"
        from_email = os.getenv("EMAIL_HOST_USER")
        recipient_list = [validated_data["email"]]

        # Trigger the Celery task
        send_email_task.delay(subject, message, from_email, recipient_list)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Incorrect Credentials")


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, data):
        self.token = data["refresh"]
        return data


class ResponseSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    refresh = serializers.CharField()
    access = serializers.CharField()


class UserCustomErrorSerializer(serializers.Serializer):
    non_field_errors = serializers.ListField(child=serializers.CharField())
