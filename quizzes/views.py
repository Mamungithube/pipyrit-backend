import random
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import QuizQuestion, QuizOption, UserQuizResult
from .serializers import QuizQuestionSerializer, UserQuizResultSerializer
from user.views import api_response

# --- APP APIs (ইউজারের জন্য) ---
class AppQuizViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = QuizQuestionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Swagger চেক করার সময় এরর এড়াতে
        if getattr(self, 'swagger_fake_view', False):
            return QuizQuestion.objects.none()

        return QuizQuestion.objects.all()

    @swagger_auto_schema(tags=['4. Quiz - App'])
    def list(self, request, *args, **kwargs):
        # শুধু লিস্ট দেখানোর সময় আমরা ২৫টি র্যান্ডম প্রশ্ন নিবো
        queryset = list(self.get_queryset())
        count = min(len(queryset), 25)
        random_questions = random.sample(queryset, count)
        
        serializer = self.get_serializer(random_questions, many=True)
        return api_response(True, f"{len(random_questions)} Questions fetched", serializer.data)

    @swagger_auto_schema(tags=['4. Quiz - App'])
    def retrieve(self, request, *args, **kwargs):
        # আইডি দিয়ে খোঁজা এখন কাজ করবে কারণ get_queryset এখন QuerySet রিটার্ন করছে
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
                # ডাটাবেস থেকে প্রশ্ন এবং অপশন চেক করা
                question = QuizQuestion.objects.get(id=q_id)
                selected_option = QuizOption.objects.get(id=o_id, question=question)
                
                if selected_option.is_correct:
                    correct_answers_count += 1
                    total_earned_points += question.points # মডেলে সেট করা পয়েন্ট যোগ হবে
            except (QuizQuestion.DoesNotExist, QuizOption.DoesNotExist):
                continue

        # রেজাল্ট সেভ করা
        result = UserQuizResult.objects.create(
            user=request.user,
            total_questions=total_questions,
            correct_answers=correct_answers_count,
            total_points_earned=total_earned_points
        )

        q_ids = [item.get('question_id') for item in user_answers]
        result.questions.set(q_ids)

        # ইউজারের প্রোফাইলে টোটাল পয়েন্ট আপডেট করা
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
        """
        এই এপিআই নির্দিষ্ট একটি কুইজ রেজাল্টের সব প্রশ্ন এবং সঠিক উত্তর দিবে।
        """
        instance = self.get_object() 
        # আপাতত সব প্রশ্ন ব্যাংক থেকে সঠিক উত্তরসহ ডাটা পাঠানোর লজিক:
        questions = QuizQuestion.objects.prefetch_related('options').all()
        data = []
        for q in questions:
            correct_option = q.options.filter(is_correct=True).first()
            data.append({
                "question": q.text,
                "answer": correct_option.text if correct_option else "N/A"
            })
        return api_response(True, "Questions and answers fetched", data)

# quizzes/views.py

class QuizResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    এই ভিউসেটটি শুধুমাত্র কুইজের ফলাফল এবং প্রশ্ন-উত্তরের লিস্ট দেখাবে।
    """
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
        instance = self.get_object() # এখন এটি UserQuizResult (আইডি ১) খুঁজে বের করবে
        questions = instance.questions.prefetch_related('options').all()
        
        data = []
        for q in questions:
            correct_option = q.options.filter(is_correct=True).first()
            data.append({
                "question": q.text,
                "answer": correct_option.text if correct_option else "N/A"
            })
        return api_response(True, "Questions and answers fetched", data)

# --- ADMIN DASHBOARD APIs (অ্যাডমিনের জন্য) ---
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