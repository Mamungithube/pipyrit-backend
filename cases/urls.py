from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CaseViewSet, CaseTypeListView

router = DefaultRouter()
router.register(r'my-cases', CaseViewSet, basename='my-cases')

urlpatterns = [
    path('types/', CaseTypeListView.as_view(), name='case-types'),
    path('', include(router.urls)),
]