from .serializers import (
    InterviewCategorySerializer, InterviewQuestionSerializer,
    InterviewResultSerializer
)
from .models import InterviewCategory, InterviewQuestion, InterviewOption, InterviewResult
from rest_framework import viewsets, status, generics
import random
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import QuizQuestion, QuizOption, UserQuizResult
from .serializers import QuizQuestionSerializer, UserQuizResultSerializer
from user.views import api_response
from user.views import CustomPagination

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
        queryset = list(self.get_queryset())
        count = min(len(queryset), 25)
        random_questions = random.sample(queryset, count)

        serializer = self.get_serializer(random_questions, many=True)
        return api_response(True, f"{len(random_questions)} Questions fetched", serializer.data)

    @swagger_auto_schema(tags=['4. Quiz - App'])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_response(True, "Question details fetched", serializer.data)

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
            return api_response(False, "No answers provided", None, status.HTTP_400_BAD_REQUEST)

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

        return api_response(True, "Quiz submitted and points calculated", data)

    @swagger_auto_schema(tags=['4. Quiz - App'])
    @action(detail=True, methods=['get'], url_path='questions-answers')
    def questions_answers(self, request, pk=None):

        instance = self.get_object()

        questions = QuizQuestion.objects.prefetch_related('options').all()
        data = []
        for q in questions:
            correct_option = q.options.filter(is_correct=True).first()
            data.append({
                "question": q.text,
                "answer": correct_option.text if correct_option else "N/A"
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
        return api_response(True, "Quiz result details fetched", serializer.data)

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
        return api_response(True, "Questions and answers fetched", data)

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


# --- APP APIs (ইউজারের জন্য) ---


class InterviewCategoryListView(generics.ListAPIView):
    queryset = InterviewCategory.objects.all()
    serializer_class = InterviewCategorySerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['5. Interview - App'])
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return api_response(True, "Interview categories fetched", serializer.data)


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
            openapi.Parameter('category_id', openapi.IN_QUERY,
                              type=openapi.TYPE_INTEGER, required=True),
            openapi.Parameter('level', openapi.IN_QUERY,
                              type=openapi.TYPE_STRING, required=True),
        ]
    )
    def list(self, request, *args, **kwargs):
        queryset = list(self.get_queryset())
        count = min(len(queryset), 25)
        random_questions = random.sample(queryset, count)
        serializer = self.get_serializer(random_questions, many=True)
        return api_response(True, f"{len(random_questions)} Questions fetched", serializer.data)
    
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
        profile.confidence_level = confidence  # লেটেস্ট কনফিডেন্স সেভ হবে
        profile.save()

        return api_response(True, "Interview submitted", InterviewResultSerializer(result).data)


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
        return api_response(True, "Interview Q&A fetched", data)
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
        return api_response(True, "Questions fetched", self.get_serializer(queryset, many=True).data)

    @swagger_auto_schema(tags=['Admin - 5. Interview Management'])
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return api_response(True, "Question and Options created", serializer.data, status.HTTP_201_CREATED)
        return api_response(False, "Failed", serializer.errors, status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=['Admin - 5. Interview Management'])
    def retrieve(self, request, *args, **kwargs):
        return api_response(True, "Details fetched", self.get_serializer(self.get_object()).data)

    @swagger_auto_schema(tags=['Admin - 5. Interview Management'])
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return api_response(True, "Updated successfully", serializer.data)
        return api_response(False, "Update failed", serializer.errors, status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=['Admin - 5. Interview Management'])
    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return api_response(True, "Deleted successfully", None, status.HTTP_204_NO_CONTENT)


# quizzes/views.py

class AdminInterviewCategoryViewSet(viewsets.ModelViewSet):

    queryset = InterviewCategory.objects.all().order_by('name')
    serializer_class = InterviewCategorySerializer
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(tags=['Admin - Interview Management'])
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return api_response(True, "Categories fetched", serializer.data)

    @swagger_auto_schema(tags=['Admin - Interview Management'])
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return api_response(True, "Category added successfully", serializer.data, status.HTTP_201_CREATED)
        return api_response(False, "Add failed", serializer.errors, status.HTTP_400_BAD_REQUEST)

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
        return api_response(True, "Category deleted successfully", None, status.HTTP_204_NO_CONTENT)