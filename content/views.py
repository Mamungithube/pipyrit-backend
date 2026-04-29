import os
import re
import time
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from drf_yasg import openapi 
from drf_yasg.utils import swagger_auto_schema

from .models import SiteSetting, VideoContent
from .serializers import SiteSettingSerializer, VideoContentSerializer
from user.views import api_response, CustomPagination 
from user.permissions import IsPremiumUser

# --- 1. APP API (User Script) ---

class AppSiteSettingView(generics.RetrieveAPIView):
    queryset = SiteSetting.objects.all()
    serializer_class = SiteSettingSerializer
    permission_classes = [AllowAny]
    lookup_field = 'key'

    @swagger_auto_schema(tags=['6. System - App'])
    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_response(True, f"{instance.title} fetched", serializer.data)


class AppVideoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = VideoContent.objects.all().order_by('-upload_date')
    serializer_class = VideoContentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination # পেজিনেশন অবজেক্টের জন্য

    @swagger_auto_schema(tags=['7. Smart Frames - App'])
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return api_response(True, "Frames list fetched", serializer.data)

    @swagger_auto_schema(tags=['7. Smart Frames - App'])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_response(True, "Frame details fetched", serializer.data)


# --- 2. ADMIN APIs (Admin Dashboard Section) ---

class AdminSiteSettingViewSet(viewsets.ModelViewSet):
    queryset = SiteSetting.objects.all()
    serializer_class = SiteSettingSerializer
    permission_classes = [IsAdminUser]
    pagination_class = CustomPagination

    def list_response(self, request, tag):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return api_response(True, "Settings list fetched", serializer.data)

    @swagger_auto_schema(tags=['Admin - System Management'])
    def list(self, request, *args, **kwargs): return self.list_response(request, 'Admin')

    @swagger_auto_schema(tags=['Admin - System Management'])
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return api_response(True, "Setting created", serializer.data, status.HTTP_201_CREATED)
        return api_response(False, "Failed", serializer.errors, status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=['Admin - System Management'])
    def retrieve(self, request, *args, **kwargs):
        return api_response(True, "Details fetched", self.get_serializer(self.get_object()).data)

    @swagger_auto_schema(tags=['Admin - System Management'])
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return api_response(True, "Updated successfully", serializer.data)
        return api_response(False, "Failed", serializer.errors, status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=['Admin - System Management'])
    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return api_response(True, "Deleted successfully", None, status.HTTP_204_NO_CONTENT)

class AdminVideoViewSet(viewsets.ModelViewSet):
    queryset = VideoContent.objects.all().order_by('-upload_date')
    serializer_class = VideoContentSerializer
    permission_classes = [IsAdminUser]
    pagination_class = CustomPagination
    parser_classes = (MultiPartParser, FormParser)

    # 1. List API (With Pagination)
    @swagger_auto_schema(tags=['Admin - Video Management'])
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return api_response(True, "Videos fetched", self.get_serializer(queryset, many=True).data)

    # 2. Create API
    @swagger_auto_schema(
        tags=['Admin - Video Management'],
        manual_parameters=[
            openapi.Parameter('thumbnail', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True),
            openapi.Parameter('video_file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True),
        ]
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return api_response(True, "Video uploaded successfully", serializer.data, status.HTTP_201_CREATED)
        return api_response(False, "Upload failed", serializer.errors, status.HTTP_400_BAD_REQUEST)

    # 3. Retrieve API
    @swagger_auto_schema(tags=['Admin - Video Management'])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_response(True, "Video details fetched", serializer.data)

    # 4. Update API
    @swagger_auto_schema(tags=['Admin - Video Management'])
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return api_response(True, "Video updated successfully", serializer.data)
        return api_response(False, "Update failed", serializer.errors, status.HTTP_400_BAD_REQUEST)

    # 5. Delete API
    @swagger_auto_schema(tags=['Admin - Video Management'])
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return api_response(True, "Video deleted successfully", None, status.HTTP_204_NO_CONTENT)


# --- 3. Other Features' APIs ---

class UserActivityHistoryView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['6. User Profile & Settings'])
    def get(self, request):
        from quizzes.models import UserQuizResult, InterviewResult
        from quizzes.serializers import UserQuizResultSerializer, InterviewResultSerializer

        quizzes = UserQuizResult.objects.filter(user=request.user).order_by('-created_at')[:10]
        interviews = InterviewResult.objects.filter(user=request.user).order_by('-created_at')[:10]

        data = {
            "quiz_history": UserQuizResultSerializer(quizzes, many=True).data,
            "interview_history": InterviewResultSerializer(interviews, many=True).data
        }
        return api_response(True, "Activity history fetched", data)


class VideoStreamView(APIView):
    permission_classes = [IsAuthenticated, IsPremiumUser] 

    def get(self, request, pk):
        video = get_object_or_404(VideoContent, pk=pk)
        path = video.video_file.path
        
        # It is better to define the file size and type in advance.
        size = os.path.getsize(path)
        content_type = 'video/mp4'
        
        range_header = request.META.get('HTTP_RANGE', '').strip()
        range_re = re.compile(r'bytes\s*=\s*(\d+)\s*-\s*(\d*)', re.I)
        range_match = range_re.match(range_header)

        if range_match:
            first_byte, last_byte = range_match.groups()
            first_byte = int(first_byte) if first_byte else 0
            last_byte = int(last_byte) if last_byte else size - 1
            if last_byte >= size:
                last_byte = size - 1
            length = last_byte - first_byte + 1
            
            def file_iterator(file_path, offset, length):
                with open(file_path, 'rb') as f:
                    f.seek(offset, os.SEEK_SET)
                    remaining = length
                    while remaining > 0:
                        data = f.read(min(remaining, 65536))
                        if not data: break
                        yield data
                        remaining -= len(data)

            response = StreamingHttpResponse(file_iterator(path, first_byte, length), status=206, content_type=content_type)
            response['Content-Range'] = f'bytes {first_byte}-{last_byte}/{size}'
            response['Content-Length'] = str(length)
        else:
            def file_iterator(file_path):
                with open(file_path, 'rb') as f:
                    while True:
                        data = f.read(8192)
                        if not data: break
                        yield data
            
            response = StreamingHttpResponse(file_iterator(path), status=200, content_type=content_type)
            response['Content-Length'] = str(size)

        response['Accept-Ranges'] = 'bytes'
        return response