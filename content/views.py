from rest_framework import viewsets, generics, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from drf_yasg.utils import swagger_auto_schema
from .models import SiteSetting
from .serializers import SiteSettingSerializer
from user.views import api_response

# --- APP APIs (ইউজার শুধু দেখতে পারবে) ---
class AppSiteSettingView(generics.RetrieveAPIView):
    queryset = SiteSetting.objects.all()
    serializer_class = SiteSettingSerializer
    permission_classes = [AllowAny] # অথবা IsAuthenticated
    lookup_field = 'key' # আইডি'র বদলে key (যেমন: privacy_policy) দিয়ে কল করা যাবে

    @swagger_auto_schema(tags=['6. System - App'])
    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_response(True, f"{instance.title} fetched", serializer.data)


# --- ADMIN APIs (অ্যাডমিন CRUD করতে পারবে) ---
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

    # এটি যোগ করলে PATCH অ্যাডমিন গ্রুপে আসবে
    @swagger_auto_schema(tags=['Admin - System Management'])
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(tags=['Admin - System Management'])
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)