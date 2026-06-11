import os

from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse


schema_view = get_schema_view(
   openapi.Info(
      title="Pipyrit API",
      default_version='v1',
      description="Pipyrit API Documentation",
      contact=openapi.Contact(email="dev.mamun50@gmail.com"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
   url=os.getenv('SWAGGER_API_URL', 'http://127.0.0.1:8000'),
)


def index(request):
    """Returns a structured JSON welcome message for the API."""
    data = {
        "message": "Welcome to the Pipyrit API!",
        "status": "healthy",
        "version": "1.0.0"
    }
    return JsonResponse(data)

urlpatterns = [
   path('', index, name='index'),
   path('admin/', admin.site.urls),
   path('api/users/', include('user.urls')),
   path('api/cases/', include('cases.urls')),
   path('api/quizzes/', include('quizzes.urls')),
   path('api/system/', include('content.urls')),
   path('api/payment/', include('payment.urls')),
   
    # Swagger Endpoints
   path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
   path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)