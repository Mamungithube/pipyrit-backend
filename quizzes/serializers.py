from rest_framework import serializers
from .models import QuizQuestion, QuizOption, UserQuizResult ,InterviewCategory, InterviewQuestion, InterviewOption, InterviewResult


class QuizOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizOption
        fields = ['id', 'text', 'is_correct']

class QuizQuestionSerializer(serializers.ModelSerializer):
    options = QuizOptionSerializer(many=True, read_only=True)

    class Meta:
        model = QuizQuestion
        fields = ['id', 'text', 'hint', 'points', 'options']

class UserQuizResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserQuizResult
        fields = ['id', 'total_questions', 'correct_answers', 'total_points_earned', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    

# interview 
class InterviewCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewCategory
        fields = ['id', 'name']

class InterviewOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewOption
        fields = ['id', 'text', 'is_correct']

class InterviewQuestionSerializer(serializers.ModelSerializer):
    options = InterviewOptionSerializer(many=True, read_only=True)

    class Meta:
        model = InterviewQuestion
        fields = ['id', 'category', 'text', 'audio_file', 'hint', 'level', 'points', 'options']

class InterviewResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewResult
        fields = [
            'id', 'category', 'level', 'total_questions', 
            'correct_answers', 'total_points_earned', 
            'confidence_level', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']