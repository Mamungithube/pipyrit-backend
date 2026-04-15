from django.db import models
from django.conf import settings

# ১. কেস টাইপ (অ্যাডমিন এটি ম্যানেজ করবে, ক্যাটাগরি ফিক্সড নয়)
class CaseType(models.Model):
    name = models.CharField(max_length=100, unique=True) # যেমন: Asylum, Green Card

    def __str__(self):
        return self.name

# ২. ইমিগ্রেশন কেস (ইউজারের মেইন ডাটা)
class ImmigrationCase(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cases')
    case_type = models.ForeignKey(CaseType, on_delete=models.SET_NULL, null=True)
    case_number = models.CharField(max_length=100, blank=True, null=True) # alien number
    title = models.CharField(max_length=255)
    last_update = models.DateField()
    status = models.CharField(max_length=100) # যেমন: Forms Mailed
    
    # Optional fields (ফিগমা অনুযায়ী)
    reminder_date = models.DateField(blank=True, null=True)
    reminder_note = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# ৩. কেস ডকুমেন্ট (ফিগমায় অপশনাল ডকুমেন্ট আপলোড আছে)
class CaseDocument(models.Model):
    case = models.ForeignKey(ImmigrationCase, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='case_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)