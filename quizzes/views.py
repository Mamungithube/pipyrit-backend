import time

from .serializers import (
    InterviewCategorySerializer, InterviewQuestionSerializer,
    InterviewResultSerializer
)
from .models import InterviewCategory, InterviewQuestion, InterviewOption, InterviewResult
from rest_framework import viewsets, status, generics
import random
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import QuizQuestion, QuizOption, UserQuizResult
from .serializers import QuizQuestionSerializer, UserQuizResultSerializer
from user.views import api_response
from user.views import CustomPagination
from django.utils.translation import gettext_lazy as _
from .ai_engine import generate_ai_quiz, generate_ai_interview
from drf_yasg import openapi

from django.shortcuts import get_object_or_404
from django.utils import timezone
"""------------------------------ Quiz Views -----------------------------"""


class AppQuizViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = QuizQuestionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return QuizQuestion.objects.none()

        return QuizQuestion.objects.all()

    @swagger_auto_schema(tags=['4. Quiz - App'])
    def list(self, request, *args, **kwargs):
        case_type = request.query_params.get('case_type')
        try:
            ai_data = generate_ai_quiz(case_type)
            questions = []
            q_ids = []
            for item in ai_data['question_set']:
                q = QuizQuestion.objects.create(text=item['question'], hint=item['hint'], explanation=item['explanation'])
                for idx, opt_text in enumerate(item['options']):
                    QuizOption.objects.create(question=q, text=opt_text, is_correct=(idx == item['correct_answer_index']))
                questions.append(q)
                q_ids.append(q.id)

            # আইডি জেনারেট করে ডাটা এর ভেতরে রাখা হলো (আগের মতো)
            result = UserQuizResult.objects.create(user=request.user, total_questions=len(questions), correct_answers=0, total_points_earned=0)
            result.questions.set(q_ids)

            serializer = self.get_serializer(questions, many=True)
            
            # আপনার আগের একদম অরিজিনাল ফরম্যাট
            return api_response(True, "Quiz started", {
                "result_id": result.id, 
                "questions": serializer.data
            })
        except Exception as e:
            return api_response(False, f"AI Error: {str(e)}", None, 500)

    @swagger_auto_schema(tags=['4. Quiz - App'])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_response(True, _("Question details fetched"), serializer.data)

    @swagger_auto_schema(
        tags=['4. Quiz - App'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'answers': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'question_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'option_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        }
                    )
                )
            }
        )
    )
    @action(detail=False, methods=['post'], url_path='submit')
    def submit_quiz(self, request):
        user_answers = request.data.get('answers', [])
        if not user_answers:
            return api_response(False, _("No answers provided"), None, status.HTTP_400_BAD_REQUEST)

        total_earned_points = 0
        correct_answers_count = 0
        total_questions = len(user_answers)

        for item in user_answers:
            q_id = item.get('question_id')
            o_id = item.get('option_id')

            try:
                question = QuizQuestion.objects.get(id=q_id)
                selected_option = QuizOption.objects.get(
                    id=o_id, question=question)

                if selected_option.is_correct:
                    correct_answers_count += 1
                    total_earned_points += question.points 
            except (QuizQuestion.DoesNotExist, QuizOption.DoesNotExist):
                continue

        result = UserQuizResult.objects.create(
            user=request.user,
            total_questions=total_questions,
            correct_answers=correct_answers_count,
            total_points_earned=total_earned_points
        )

        q_ids = [item.get('question_id') for item in user_answers]
        result.questions.set(q_ids)

        profile = request.user.profile
        profile.total_points += total_earned_points
        profile.save()

        data = {
            "correct_answers": correct_answers_count,
            "total_questions": total_questions,
            "points_earned": total_earned_points,
            "total_profile_points": profile.total_points
        }

        return api_response(True, _("Quiz submitted and points calculated"), data)

    @swagger_auto_schema(
        tags=['4. Quiz - App'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'result_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID received from GET /quick-quiz/"), # এটি যোগ করুন
                'correct_answers': openapi.Schema(type=openapi.TYPE_INTEGER),
                'total_questions': openapi.Schema(type=openapi.TYPE_INTEGER),
                'earned_points': openapi.Schema(type=openapi.TYPE_INTEGER),
            },
            required=['result_id'] # আইডি পাঠানো বাধ্যতামূলক
        )
    )
    @action(detail=False, methods=['post'], url_path='save-score')
    def save_score(self, request):
        res_id = request.data.get('result_id')
        result = get_object_or_404(UserQuizResult, id=res_id, user=request.user)
        result.correct_answers = request.data.get('correct_answers', 0)
        result.total_points_earned = request.data.get('earned_points', 0)
        result.save()
        
        profile = request.user.profile
        profile.total_points += result.total_points_earned
        profile.save()
        return api_response(True, "Quiz score saved", {"id": result.id})

    @swagger_auto_schema(tags=['4. Quiz - App'])
    def questions_answers(self, request, pk=None):
        """
        GET /api/quizzes/quick-quiz/{id}/questions-answers/
        এখানে {id} হলো UserQuizResult এর আইডি (যা হিস্ট্রি থেকে পাওয়া যাবে)
        """
        instance = get_object_or_404(UserQuizResult, id=pk, user=request.user)
        questions = instance.questions.all()
        
        data = []
        for q in questions:
            correct_opt = q.options.filter(is_correct=True).first()
            data.append({
                "question": q.text,
                "answer": correct_opt.text if correct_opt else "N/A",
                "explanation": q.explanation
            })
        
        return api_response(True, "Questions and answers fetched", data)



class QuizResultViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = UserQuizResultSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return UserQuizResult.objects.none()
        return UserQuizResult.objects.filter(user=self.request.user).order_by('-created_at')

    @swagger_auto_schema(tags=['4. Quiz - App'])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=['4. Quiz - App'])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_response(True, _("Quiz result details fetched"), serializer.data)

    @swagger_auto_schema(tags=['4. Quiz - App'])
    @action(detail=True, methods=['get'], url_path='questions-answers')
    def questions_answers(self, request, pk=None):
        instance = self.get_object()  
        questions = instance.questions.prefetch_related('options').all()

        data = []
        for q in questions:
            correct_option = q.options.filter(is_correct=True).first()
            data.append({
                "question": q.text,
                "answer": correct_option.text if correct_option else "N/A"
            })
        return api_response(True, _("Questions and answers fetched"), data)

# ---------------------- ADMIN DASHBOARD APIs -----------------------


class AdminQuizManagementViewSet(viewsets.ModelViewSet):
    queryset = QuizQuestion.objects.all().order_by('-created_at')
    serializer_class = QuizQuestionSerializer
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(tags=['Admin - Quiz Management'])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=['Admin - Quiz Management'])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(tags=['Admin - Quiz Management'])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(tags=['Admin - Quiz Management'])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(tags=['Admin - Quiz Management'])
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(tags=['Admin - Quiz Management'])
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


"""----------------------------- Interview Quiz -----------------------------"""


# --- APP APIs (for users) ---


class InterviewCategoryListView(generics.ListAPIView):
    queryset = InterviewCategory.objects.all()
    serializer_class = InterviewCategorySerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['5. Interview - App'])
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return api_response(True, _("Interview categories fetched"), serializer.data)


class AppInterviewViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InterviewQuestionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return InterviewQuestion.objects.none()

        category_id = self.request.query_params.get('category_id')
        level = self.request.query_params.get(
            'level')  # beginner/intermediate/advanced

        queryset = InterviewQuestion.objects.all()
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if level:
            queryset = queryset.filter(level=level)
        return queryset

    @swagger_auto_schema(
        tags=['5. Interview - App'],
        manual_parameters=[
            openapi.Parameter('category', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('level', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
        ]
    )
    def list(self, request, *args, **kwargs):
        category_name = request.query_params.get('category')
        level = request.query_params.get('level')
        try:
            ai_data = generate_ai_interview(category_name, level)
            cat_obj, _ = InterviewCategory.objects.get_or_create(name=category_name)
            questions = []
            q_ids = []
            for item in ai_data['question_set']:
                iq = InterviewQuestion.objects.create(category=cat_obj, text=item['question'], level=level, hint=item.get('hint', ''), explanation=item.get('explanation', ''), example=item.get('example', ''))
                for idx, opt_text in enumerate(item['options']):
                    InterviewOption.objects.create(question=iq, text=opt_text, is_correct=(idx == item['correct_response_index']))
                questions.append(iq)
                q_ids.append(iq.id)

            result = InterviewResult.objects.create(user=request.user, category=cat_obj, level=level, total_questions=len(questions), correct_answers=0, total_points_earned=0)
            result.questions.set(q_ids)

            serializer = self.get_serializer(questions, many=True)
            
            # এটি আপনার চাওয়া স্পেশাল ফরম্যাট: result_id ডাটার বাইরে
            return Response({
                "code": 200,
                "success": True,
                "message": "Interview generated",
                "result_id": result.id,  # <--- ডাটা এর বাইরে
                "timestamp": int(time.time()),
                "data": serializer.data 
            })
        except Exception as e:
            return api_response(False, f"AI Error: {str(e)}", None, 500)

    @swagger_auto_schema(tags=['5. Interview - App'])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['5. Interview - App'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'category_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'level': openapi.Schema(type=openapi.TYPE_STRING),
                'answers': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'question_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'option_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        }
                    )
                )
            }
        )
    )
    @action(detail=False, methods=['post'], url_path='submit')
    def submit_interview(self, request):
        category_id = request.data.get('category_id')
        level = request.data.get('level')
        user_answers = request.data.get('answers', [])

        total_earned_points = 0
        correct_answers_count = 0
        q_ids = []

        for item in user_answers:
            q_id = item.get('question_id')
            o_id = item.get('option_id')
            q_ids.append(q_id)
            try:
                question = InterviewQuestion.objects.get(id=q_id)
                selected_option = InterviewOption.objects.get(
                    id=o_id, question=question)
                if selected_option.is_correct:
                    correct_answers_count += 1
                    total_earned_points += question.points
            except:
                continue

        total_qs = len(user_answers) if len(user_answers) > 0 else 1
        confidence = int((correct_answers_count / total_qs) * 100)

        result = InterviewResult.objects.create(
            user=request.user,
            category_id=category_id,
            level=level,
            total_questions=len(user_answers),
            correct_answers=correct_answers_count,
            total_points_earned=total_earned_points,
            confidence_level=confidence
        )
        result.questions.set(q_ids)

        profile = request.user.profile
        profile.total_points += total_earned_points
        profile.confidence_level = confidence  # The latest confidence will be saved.
        profile.save()

        return api_response(True, _("Interview submitted"), InterviewResultSerializer(result).data)
    
    @swagger_auto_schema(
        tags=['5. Interview - App'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'result_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID received from GET /interview-process/"), # এটি যোগ করুন
                'correct_answers': openapi.Schema(type=openapi.TYPE_INTEGER),
                'total_questions': openapi.Schema(type=openapi.TYPE_INTEGER),
                'earned_points': openapi.Schema(type=openapi.TYPE_INTEGER),
                'confidence_level': openapi.Schema(type=openapi.TYPE_INTEGER),
            },
            required=['result_id'] # আইডি পাঠানো বাধ্যতামূলক
        )
    )
    @action(detail=False, methods=['post'], url_path='save-score')
    def save_score(self, request):
        cat_id = request.data.get('category_id')
        correct = request.data.get('correct_answers', 0)
        total = request.data.get('total_questions', 25)
        points = request.data.get('earned_points', 0)
        confidence = request.data.get('confidence_level', 0)

        result = InterviewResult.objects.create(
            user=request.user,
            category_id=cat_id,
            total_questions=total,
            correct_answers=correct,
            total_points_earned=points,
            confidence_level=confidence
        )

        # প্রোফাইল আপডেট
        profile = request.user.profile
        profile.total_points += points
        profile.confidence_level = confidence
        profile.save()

        return api_response(True, "Interview result saved", {"id": result.id})


class InterviewResultViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = InterviewResultSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return InterviewResult.objects.none()
        return InterviewResult.objects.filter(user=self.request.user).order_by('-created_at')

    @swagger_auto_schema(tags=['5. Interview - App'])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(tags=['5. Interview - App'])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(tags=['5. Interview - App'])
    @action(detail=True, methods=['get'], url_path='questions-answers')
    def questions_answers(self, request, pk=None):
        instance = self.get_object()
        questions = instance.questions.prefetch_related('options').all()
        data = []
        for q in questions:
            correct_option = q.options.filter(is_correct=True).first()
            data.append({
                "question": q.text,
                "answer": correct_option.text if correct_option else "N/A"
            })
        return api_response(True, _("Interview Q&A fetched"), data)
# --- ADMIN APIs ---


class AdminInterviewQuestionViewSet(viewsets.ModelViewSet):
    queryset = InterviewQuestion.objects.all().order_by('-created_at')
    serializer_class = InterviewQuestionSerializer
    permission_classes = [IsAdminUser]
    pagination_class = CustomPagination

    @swagger_auto_schema(tags=['Admin - 5. Interview Management'])
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return api_response(True, _("Questions fetched"), self.get_serializer(queryset, many=True).data)

    @swagger_auto_schema(tags=['Admin - 5. Interview Management'])
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return api_response(True, _("Question and Options created"), serializer.data, status.HTTP_201_CREATED)
        return api_response(False, _("Failed"), serializer.errors, status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=['Admin - 5. Interview Management'])
    def retrieve(self, request, *args, **kwargs):
        return api_response(True, _("Details fetched"), self.get_serializer(self.get_object()).data)

    @swagger_auto_schema(tags=['Admin - 5. Interview Management'])
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return api_response(True, _("Updated successfully"), serializer.data)
        return api_response(False, _("Update failed"), serializer.errors, status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=['Admin - 5. Interview Management'])
    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return api_response(True, _("Deleted successfully"), None, status.HTTP_204_NO_CONTENT)


# quizzes/views.py

class AdminInterviewCategoryViewSet(viewsets.ModelViewSet):

    queryset = InterviewCategory.objects.all().order_by('name')
    serializer_class = InterviewCategorySerializer
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(tags=['Admin - Interview Management'])
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return api_response(True, _("Categories fetched"), serializer.data)

    @swagger_auto_schema(tags=['Admin - Interview Management'])
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return api_response(True, _("Category added successfully"), serializer.data, status.HTTP_201_CREATED)
        return api_response(False, _("Add failed"), serializer.errors, status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=['Admin - Interview Management'])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(tags=['Admin - Interview Management'])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(tags=['Admin - Interview Management'])
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(tags=['Admin - Interview Management'])
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return api_response(True, _("Category deleted successfully"), None, status.HTTP_204_NO_CONTENT)