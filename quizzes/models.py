
from django.db import models
from django.conf import settings

# কুইজের মেইন প্রশ্ন ব্যাংক
class QuizQuestion(models.Model):
    text = models.TextField() 
    hint = models.TextField(blank=True, null=True)
    points = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text[:50]

class QuizOption(models.Model):
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

class UserQuizResult(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    questions = models.ManyToManyField(QuizQuestion, related_name='quiz_results')
    total_questions = models.IntegerField(default=25)
    correct_answers = models.IntegerField()
    total_points_earned = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)