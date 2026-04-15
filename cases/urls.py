from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CaseViewSet, CaseTypeListView, AdminCaseTypeViewSet

router = DefaultRouter()
router.register(r'my-cases', CaseViewSet, basename='my-cases')
router.register(r'admin/case-types', AdminCaseTypeViewSet, basename='admin-case-types')

urlpatterns = [
    path('types/', CaseTypeListView.as_view(), name='case-types'),

    path('', include(router.urls)),
]