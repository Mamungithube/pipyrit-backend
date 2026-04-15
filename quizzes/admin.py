from django.contrib import admin
from .models import QuizQuestion, QuizOption, UserQuizResult

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