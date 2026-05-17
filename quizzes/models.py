
from io import BytesIO
from time import time

from django.db import models
from django.conf import settings
import os
from gtts import gTTS
from django.db import models
from django.conf import settings
from django.core.files.base import ContentFile

# Create your models here.

# অডিও জেনারেট করার জন্য একটি হেল্পার ফাংশন
def generate_tts_audio(text, lang='en'):
    tts = gTTS(text=text, lang=lang)
    audio_buffer = BytesIO()
    tts.write_to_fp(audio_buffer)
    return ContentFile(audio_buffer.getvalue())

# ----------------Quiz models----------
class QuizQuestion(models.Model):
    text = models.TextField() 
    audio_file = models.FileField(upload_to='quiz_audio/', blank=True, null=True)
    hint = models.TextField(blank=True, null=True)
    points = models.IntegerField(default=1)
    explanation = models.TextField(blank=True, null=True) 
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # যদি প্রশ্ন নতুন হয় এবং টেক্সট থাকে, তবেই অডিও জেনারেট হবে
        if not self.audio_file and self.text:
            from django.utils import timezone # লোকাল ইম্পোর্ট সেফটি
            audio_content = generate_tts_audio(self.text)
            # time.time() এর বদলে timezone.now().timestamp() ব্যবহার করা হয়েছে
            timestamp = int(timezone.now().timestamp())
            self.audio_file.save(f"quiz_{timestamp}.mp3", audio_content, save=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.text[:50]

class QuizOption(models.Model):
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=500)
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


# --------------interview models---------------
class InterviewCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

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
    points = models.IntegerField(default=25) 
    explanation = models.TextField(blank=True, null=True)
    example = models.TextField(blank=True, null=True) 
    
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # অটোমেটিক ইন্টারভিউ অডিও জেনারেট
        if not self.audio_file and self.text:
            from django.utils import timezone
            audio_content = generate_tts_audio(self.text)
            # এখানেও টাইমস্ট্যাম্প লজিক আপডেট করা হয়েছে
            timestamp = int(timezone.now().timestamp())
            self.audio_file.save(f"interview_{timestamp}.mp3", audio_content, save=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.level}] {self.text[:50]}"

class InterviewOption(models.Model):
    question = models.ForeignKey(InterviewQuestion, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

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