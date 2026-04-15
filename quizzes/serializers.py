from rest_framework import serializers
from .models import QuizQuestion, QuizOption, UserQuizResult ,InterviewCategory, InterviewQuestion, InterviewOption, InterviewResult

# ১. প্রশ্নের অপশনগুলোর জন্য
class QuizOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizOption
        fields = ['id', 'text', 'is_correct']

# ২. কুইজের মেইন প্রশ্ন এবং তার সাথে অপশনগুলো দেখানোর জন্য
class QuizQuestionSerializer(serializers.ModelSerializer):
    options = QuizOptionSerializer(many=True, read_only=True)

    class Meta:
        model = QuizQuestion
        fields = ['id', 'text', 'hint', 'points', 'options']

# ৩. কুইজ শেষে রেজাল্ট সেভ করার জন্য
class UserQuizResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserQuizResult
        fields = ['id', 'total_questions', 'correct_answers', 'total_points_earned', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    

# interview এর জন্য কুইজের প্রশ্ন এবং অপশন সিরিয়ালাইজার

# ১. ইন্টারভিউ ক্যাটাগরি সিরিয়ালাইজার
class InterviewCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewCategory
        fields = ['id', 'name']

# ২. প্রশ্নের অপশন সিরিয়ালাইজার
class InterviewOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewOption
        fields = ['id', 'text', 'is_correct']

# ৩. ইন্টারভিউ প্রশ্ন সিরিয়ালাইজার (অপশনসহ)
class InterviewQuestionSerializer(serializers.ModelSerializer):
    options = InterviewOptionSerializer(many=True, read_only=True)

    class Meta:
        model = InterviewQuestion
        fields = ['id', 'category', 'text', 'audio_file', 'hint', 'level', 'points', 'options']

# ৪. ইন্টারভিউ রেজাল্ট সিরিয়ালাইজার
class InterviewResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewResult
        fields = [
            'id', 'category', 'level', 'total_questions', 
            'correct_answers', 'total_points_earned', 
            'confidence_level', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']