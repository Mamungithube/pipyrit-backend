import os

from django.contrib import admin
from django.urls import path, re_path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.views.static import serve

from core.views import api_root, health_check  
from pipyrit.root_auth import basic_auth_required


def custom_serve_media(request, path):
    full_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(full_path):
        response = serve(request, path, document_root=settings.MEDIA_ROOT)
    else:
        fallback_path = os.path.join(settings.BASE_DIR, path)
        if os.path.exists(fallback_path):
            response = serve(request, path, document_root=settings.BASE_DIR)
        else:
            response = serve(request, path, document_root=settings.MEDIA_ROOT)

    if response.status_code == 200:
        response['Cache-Control'] = 'public, max-age=86400'
    return response


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

urlpatterns = [
   path('', api_root, name='index'),        
   path('health/', health_check, name='health-check'),  
   path('admin/', admin.site.urls),
   path('api/users/', include('user.urls')),
   path('api/cases/', include('cases.urls')),
   path('api/quizzes/', include('quizzes.urls')),
   path('api/system/', include('content.urls')),
   path('api/payment/', include('payment.urls')),

    # Swagger Endpoints
   path('swagger/', basic_auth_required(schema_view.with_ui('swagger', cache_timeout=0)), name='schema-swagger-ui'),
   path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
   re_path(r'^media/(?P<path>.*)$', custom_serve_media),
]