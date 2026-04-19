from rest_framework import serializers
from .models import QuizQuestion, QuizOption, UserQuizResult ,InterviewCategory, InterviewQuestion, InterviewOption, InterviewResult


class QuizOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizOption
        fields = ['id', 'text', 'is_correct']

class QuizQuestionSerializer(serializers.ModelSerializer):
    options = QuizOptionSerializer(many=True)

    class Meta:
        model = QuizQuestion
        fields = ['id', 'text', 'hint', 'points', 'options']

    def create(self, validated_data):
        options_data = validated_data.pop('options', [])

        if not options_data:
            raise serializers.ValidationError({"options": "At least one option is required."})

        question = QuizQuestion.objects.create(**validated_data)
        for option_data in options_data:
            QuizOption.objects.create(question=question, **option_data)
        return question

    def update(self, instance, validated_data):
        options_data = validated_data.pop('options', None)
        instance = super().update(instance, validated_data)

        if options_data is not None:
            instance.options.all().delete()
            for option_data in options_data:
                QuizOption.objects.create(question=instance, **option_data)
        return instance

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
    options = InterviewOptionSerializer(many=True)

    class Meta:
        model = InterviewQuestion
        fields = ['id', 'category', 'text', 'hint', 'level', 'points', 'options']

    def create(self, validated_data):
        # pop করার সময় ডিফল্ট খালি লিস্ট দিন যাতে KeyError না আসে
        options_data = validated_data.pop('options', [])
        
        if not options_data:
            raise serializers.ValidationError({"options": "At least one option is required."})
            
        question = InterviewQuestion.objects.create(**validated_data)
        for option_data in options_data:
            InterviewOption.objects.create(question=question, **option_data)
        return question

    def update(self, instance, validated_data):
        options_data = validated_data.pop('options', None)
        # মেইন প্রশ্ন আপডেট
        instance = super().update(instance, validated_data)
        
        # অপশন আপডেট (পুরানো গুলো মুছে নতুন গুলো সেভ করা সহজ উপায়)
        if options_data is not None:
            instance.options.all().delete()
            for option_data in options_data:
                InterviewOption.objects.create(question=instance, **option_data)
        return instance

class InterviewResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewResult
        fields = [
            'id', 'category', 'level', 'total_questions', 
            'correct_answers', 'total_points_earned', 
            'confidence_level', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']