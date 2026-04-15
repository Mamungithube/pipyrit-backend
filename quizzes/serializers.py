from rest_framework import serializers
from .models import QuizQuestion, QuizOption, UserQuizResult

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