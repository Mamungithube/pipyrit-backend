from django.contrib import admin
from .models import QuizQuestion, QuizOption, UserQuizResult, InterviewCategory, InterviewQuestion, InterviewOption, InterviewResult

# প্রশ্নের সাথে অপশনগুলো ইনলাইন হিসেবে দেখানোর জন্য
class QuizOptionInline(admin.TabularInline):
    model = QuizOption
    extra = 4  # ডিফল্টভাবে ৪টি অপশন ইনপুট বক্স দেখাবে
    max_num = 4 # সর্বোচ্চ ৪টি অপশন

@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'points', 'created_at']
    search_fields = ['text']
    inlines = [QuizOptionInline]

@admin.register(UserQuizResult)
class UserQuizResultAdmin(admin.ModelAdmin):
    list_display = ['user', 'correct_answers', 'total_points_earned', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'user__full_name']

# যদি আলাদাভাবে অপশন ম্যানেজ করতে চান (ঐচ্ছিক)
# admin.site.register(QuizOption)

# ক্যাটাগরি ম্যানেজমেন্ট
@admin.register(InterviewCategory)
class InterviewCategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']

# প্রশ্নের সাথে অপশন ইনলাইন
class InterviewOptionInline(admin.TabularInline):
    model = InterviewOption
    extra = 4
    max_num = 4

# মেইন প্রশ্ন ম্যানেজমেন্ট
@admin.register(InterviewQuestion)
class InterviewQuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'category', 'level', 'points', 'created_at']
    list_filter = ['category', 'level', 'created_at'] # ফিল্টার করার জন্য
    search_fields = ['text']
    inlines = [InterviewOptionInline]

# রেজাল্ট হিস্ট্রি ম্যানেজমেন্ট
@admin.register(InterviewResult)
class InterviewResultAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'level', 'total_points_earned', 'confidence_level', 'created_at']
    list_filter = ['level', 'category', 'created_at']
    search_fields = ['user__email', 'user__full_name']
    readonly_fields = ['created_at'] # রেজাল্ট যেন অ্যাডমিন এডিট না করতে পারে