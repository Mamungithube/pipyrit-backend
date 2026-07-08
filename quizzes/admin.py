from django.contrib import admin
from .models import QuizQuestion, QuizOption, UserQuizResult, InterviewCategory, InterviewQuestion, InterviewOption, InterviewResult

class QuizOptionInline(admin.TabularInline):
    model = QuizOption
    extra = 4  
    max_num = 4 

@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ['id','text', 'points', 'created_at']
    search_fields = ['text']
    inlines = [QuizOptionInline]

@admin.register(UserQuizResult)
class UserQuizResultAdmin(admin.ModelAdmin):
    list_display = ['id','user', 'correct_answers', 'total_points_earned','confidence_level', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'user__full_name']


@admin.register(InterviewCategory)
class InterviewCategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']

class InterviewOptionInline(admin.TabularInline):
    model = InterviewOption
    extra = 4
    max_num = 4


@admin.register(InterviewQuestion)
class InterviewQuestionAdmin(admin.ModelAdmin):
    list_display = ['id','text', 'category', 'level', 'points', 'created_at']
    list_filter = ['category', 'level', 'created_at']
    search_fields = ['text']
    inlines = [InterviewOptionInline]

@admin.register(InterviewResult)
class InterviewResultAdmin(admin.ModelAdmin):
    list_display = ['id','user', 'category', 'level', 'total_points_earned', 'confidence_level', 'created_at']
    list_filter = ['level', 'category', 'created_at']
    search_fields = ['user__email', 'user__full_name']
    readonly_fields = ['created_at'] 