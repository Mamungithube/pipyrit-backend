from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AppSiteSettingView, AdminSiteSettingViewSet , AdminVideoViewSet, AppVideoViewSet , VideoStreamView

router = DefaultRouter()
router.register(r'admin/settings', AdminSiteSettingViewSet, basename='admin-settings')
router.register(r'admin/videos', AdminVideoViewSet, basename='admin-videos')
router.register(r'app/videos', AppVideoViewSet, basename='app-videos')


urlpatterns = [
    path('legal/<str:key>/', AppSiteSettingView.as_view(), name='app-legal-content'),
    path('stream/<int:pk>/', VideoStreamView.as_view(), name='video-stream'),
    
    path('', include(router.urls)),
]