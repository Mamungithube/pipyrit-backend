
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


# interview এর জন্য কুইজের প্রশ্ন এবং অপশন মডেল
class InterviewCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

# ২. ইন্টারভিউ প্রশ্ন ব্যাংক (ক্যাটাগরি এবং লেভেল অনুযায়ী ফিল্টার হবে)
class InterviewQuestion(models.Model):
    LEVEL_CHOICES = (
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    )

    category = models.ForeignKey(InterviewCategory, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    audio_file = models.FileField(upload_to='interview_audio/', blank=True, null=True) # Listen বাটন
    hint = models.TextField(blank=True, null=True) 
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    points = models.IntegerField(default=5) 
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.level}] {self.text[:50]}"

# ৩. ইন্টারভিউ অপশন
class InterviewOption(models.Model):
    question = models.ForeignKey(InterviewQuestion, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

# ৪. ইন্টারভিউ রেজাল্ট (Confidence Level সহ)
class InterviewResult(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(InterviewCategory, on_delete=models.SET_NULL, null=True)
    level = models.CharField(max_length=20) # Beginner, Intermediate, Advanced
    
    total_questions = models.IntegerField(default=25)
    correct_answers = models.IntegerField()
    total_points_earned = models.IntegerField()
    
    confidence_level = models.IntegerField(default=0) 

    questions = models.ManyToManyField(InterviewQuestion, related_name='interview_results')
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.category.name} ({self.level})"