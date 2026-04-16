from django.db import models

class SiteSetting(models.Model):
    KEY_CHOICES = (
        ('privacy_policy', 'Privacy Policy'),
        ('terms_conditions', 'Terms & Conditions'),
        ('about_us', 'About Us'),
    )
    key = models.CharField(max_length=50, choices=KEY_CHOICES, unique=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title