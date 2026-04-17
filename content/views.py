from drf_spectacular import openapi
from rest_framework import viewsets, generics, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from drf_yasg import openapi 
from drf_yasg.utils import swagger_auto_schema
from .models import SiteSetting, VideoContent
from .serializers import SiteSettingSerializer, VideoContentSerializer
from user.views import api_response
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
import os
import re


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


class AdminSiteSettingViewSet(viewsets.ModelViewSet):
    queryset = SiteSetting.objects.all()
    serializer_class = SiteSettingSerializer
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(tags=['Admin - System Management'])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=['Admin - System Management'])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    # এটি যোগ করলে GET by ID অ্যাডমিন গ্রুপে আসবে
    @swagger_auto_schema(tags=['Admin - System Management'])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(tags=['Admin - System Management'])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(tags=['Admin - System Management'])
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(tags=['Admin - System Management'])
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class AdminVideoViewSet(viewsets.ModelViewSet):
    queryset = VideoContent.objects.all().order_by('-upload_date')
    serializer_class = VideoContentSerializer
    permission_classes = [IsAdminUser]
    parser_classes = (MultiPartParser, FormParser)

    @swagger_auto_schema(
        tags=['Admin - Video Management'],
        manual_parameters=[
            openapi.Parameter('thumbnail', openapi.IN_FORM,
                              type=openapi.TYPE_FILE, description="Upload Thumbnail"),
            openapi.Parameter('video_file', openapi.IN_FORM,
                              type=openapi.TYPE_FILE, description="Upload Video"),
        ]
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class AppVideoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = VideoContent.objects.all().order_by('-upload_date')
    serializer_class = VideoContentSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['7. Smart Frames - App'])
    def list(self, request, *args, **
             kwargs): return super().list(request, *args, **kwargs)


class UserActivityHistoryView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['6. User Profile & Settings'])
    def get(self, request):
        from quizzes.models import UserQuizResult, InterviewResult
        from quizzes.serializers import UserQuizResultSerializer, InterviewResultSerializer

        quizzes = UserQuizResult.objects.filter(
            user=request.user).order_by('-created_at')[:10]
        interviews = InterviewResult.objects.filter(
            user=request.user).order_by('-created_at')[:10]

        data = {
            "quiz_history": UserQuizResultSerializer(quizzes, many=True).data,
            "interview_history": InterviewResultSerializer(interviews, many=True).data
        }
        return api_response(True, "Activity history fetched", data)



class VideoStreamView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        video = get_object_or_404(VideoContent, pk=pk)
        path = video.video_file.path
        
        range_header = request.META.get('HTTP_RANGE', '').strip()
        range_re = re.compile(r'bytes\s*=\s*(\d+)\s*-\s*(\d*)', re.I)
        range_match = range_re.match(range_header)
        
        size = os.path.getsize(path)
        content_type = 'video/mp4'

        if range_match:
            first_byte, last_byte = range_match.groups()
            first_byte = int(first_byte) if first_byte else 0
            last_byte = int(last_byte) if last_byte else size - 1
            if last_byte >= size: last_byte = size - 1
            length = last_byte - first_byte + 1
            
            def file_iterator(file_path, offset, length, chunk_size=8192):
                with open(file_path, 'rb') as f:
                    f.seek(offset, os.SEEK_SET)
                    remaining = length
                    while remaining > 0:
                        bytes_to_read = min(remaining, chunk_size)
                        data = f.read(bytes_to_read)
                        if not data: break
                        yield data
                        remaining -= len(data)

            response = StreamingHttpResponse(file_iterator(path, first_byte, length), status=206, content_type=content_type)
            response['Content-Range'] = f'bytes {first_byte}-{last_byte}/{size}'
            response['Accept-Ranges'] = 'bytes'
            response['Content-Length'] = str(length)
        else:
            def file_iterator(file_path, chunk_size=8192):
                with open(file_path, 'rb') as f:
                    while True:
                        data = f.read(chunk_size)
                        if not data: break
                        yield data

            response = StreamingHttpResponse(file_iterator(path), content_type=content_type)
            response['Content-Length'] = str(size)
            response['Accept-Ranges'] = 'bytes'

        return response