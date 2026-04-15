from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    # Quiz Views
    AppQuizViewSet, AdminQuizManagementViewSet, QuizResultViewSet,
    # Interview Views
    InterviewCategoryListView, AppInterviewViewSet, 
    AdminInterviewQuestionViewSet, InterviewResultViewSet,AdminInterviewCategoryViewSet
)

router = DefaultRouter()

# --- 1. QUIZ Endpoints ---
router.register(r'quick-quiz', AppQuizViewSet, basename='quick-quiz')
router.register(r'quiz-results', QuizResultViewSet, basename='quiz-results') 
router.register(r'admin/quiz-questions', AdminQuizManagementViewSet, basename='admin-quiz-questions')

# --- 2. INTERVIEW Endpoints ---
router.register(r'interview-process', AppInterviewViewSet, basename='interview-process')
router.register(r'interview-results', InterviewResultViewSet, basename='interview-results') 
router.register(r'admin/interview-questions', AdminInterviewQuestionViewSet, basename='admin-interview-questions')
router.register(r'admin/interview-categories', AdminInterviewCategoryViewSet, basename='admin-interview-categories')

urlpatterns = [
    # ইন্টারভিউ ক্যাটাগরি লিস্ট (যেমন: Marriage, Asylum)
    path('interview-categories/', InterviewCategoryListView.as_view(), name='interview-categories'),
    
    # সব রাউটার এন্ডপয়েন্ট একসাথে
    path('', include(router.urls)),
]