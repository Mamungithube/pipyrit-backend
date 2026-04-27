from django.db import models
from django.conf import settings

class CaseType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class ImmigrationCase(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cases')
    case_type = models.ForeignKey(CaseType, on_delete=models.SET_NULL, null=True)
    case_number = models.CharField(max_length=100, blank=True, null=True) 
    title = models.CharField(max_length=255)
    last_update = models.DateField()
    status = models.CharField(max_length=100)
    reminder_date = models.DateField(blank=True, null=True)
    reminder_note = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class CaseDocument(models.Model):
    case = models.ForeignKey(ImmigrationCase, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='case_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)