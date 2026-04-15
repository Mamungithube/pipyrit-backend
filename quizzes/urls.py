from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AppQuizViewSet, AdminQuizManagementViewSet, QuizResultViewSet

router = DefaultRouter()

# অ্যাপ এপিআই (২৫টা প্রশ্ন পেতে এবং সাবমিট করতে)
router.register(r'quick-quiz', AppQuizViewSet, basename='quick-quiz')
router.register(r'results', QuizResultViewSet, basename='quiz-results') 
# অ্যাডমিন এপিআই (ড্যাশবোর্ড থেকে প্রশ্ন ম্যানেজ করতে)
router.register(r'admin/questions', AdminQuizManagementViewSet, basename='admin-questions')

urlpatterns = [
    path('', include(router.urls)),
]