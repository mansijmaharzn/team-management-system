import os
import logging
from pathlib import Path
from dotenv import load_dotenv

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema, OpenApiResponse

from users.serializers import (
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    LogoutSerializer,
    ResponseSerializer,
    UserCustomErrorSerializer,
)

from users.tasks import send_email_task


env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)


logger = logging.getLogger(__name__)


class RegisterAPI(APIView):
    serializer_class = RegisterSerializer

    @extend_schema(
        request=RegisterSerializer,
        responses={
            200: OpenApiResponse(
                response=ResponseSerializer, description="Successful Login"
            ),
            400: OpenApiResponse(
                response=UserCustomErrorSerializer, description="Failed Login"
            ),
        },
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            logger.info(f"User {user.username} registered")

            subject = "Thanks for creating account!"
            message = "We would expect you to view this email ;)"
            from_email = os.getenv("EMAIL_HOST_USER")
            recipient_list = [serializer.validated_data["email"]]

            # Trigger the Celery task
            send_email_task.delay(subject, message, from_email, recipient_list)

            return Response(
                {
                    "user": user.id,
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                status=status.HTTP_201_CREATED,
            )

        logger.warning(f"Failed to register user: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPI(APIView):
    serializer_class = LoginSerializer

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                response=ResponseSerializer, description="Successful Login"
            ),
            400: OpenApiResponse(
                response=UserCustomErrorSerializer, description="Failed Login"
            ),
        },
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            refresh = RefreshToken.for_user(user)
            logger.info(f"User {user.username} logged in")

            return Response(
                {
                    "user": user.id,
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                status=status.HTTP_200_OK,
            )

        logger.warning(f"Failed to login user: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserAPI(APIView):
    serializer = UserSerializer

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=UserSerializer, description="User data retrieved successfully"
            ),
            404: OpenApiResponse(
                response=UserCustomErrorSerializer, description="User not found"
            ),
        }
    )
    def get(self, request, *args, **kwargs):
        user_id = kwargs.get("user_id")
        try:
            user = User.objects.get(id=user_id)
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist as e:
            return Response(
                {"non_field_errors": [str(e)]}, status=status.HTTP_404_NOT_FOUND
            )


class LogoutAPI(APIView):
    serializer_class = LogoutSerializer

    def post(self, request):
        refresh_token = request.data.get("refresh")
        token = RefreshToken(refresh_token)
        token.blacklist()
        logger.info(f"User {request.user.username} logged out and token blacklisted")
        return Response(status=status.HTTP_200_OK)
