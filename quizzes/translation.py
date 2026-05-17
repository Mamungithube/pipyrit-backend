from modeltranslation.translator import register, TranslationOptions
from .models import QuizQuestion, QuizOption, InterviewCategory, InterviewQuestion, InterviewOption

# ১. কুইজ প্রশ্ন ও হিন্ট অনুবাদ
@register(QuizQuestion)
class QuizQuestionTranslationOptions(TranslationOptions):
    fields = ('text', 'hint') # প্রশ্ন এবং হিন্ট দুইটাই অনুবাদ হবে

# ২. কুইজ অপশন অনুবাদ (খুবই জরুরি)
@register(QuizOption)
class QuizOptionTranslationOptions(TranslationOptions):
    fields = ('text',)

# ৩. ইন্টারভিউ ক্যাটাগরি অনুবাদ
@register(InterviewCategory)
class InterviewCategoryTranslationOptions(TranslationOptions):
    fields = ('name',)

# ৪. ইন্টারভিউ প্রশ্ন ও হিন্ট অনুবাদ
@register(InterviewQuestion)
class InterviewQuestionTranslationOptions(TranslationOptions):
    fields = ('text', 'hint')

# ৫. ইন্টারভিউ অপশন অনুবাদ
@register(InterviewOption)
class InterviewOptionTranslationOptions(TranslationOptions):
    fields = ('text',)