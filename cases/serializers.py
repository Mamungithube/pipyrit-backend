from rest_framework import serializers
from .models import ImmigrationCase, CaseType, CaseDocument

class CaseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseType
        fields = ['id', 'name']

class CaseDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseDocument
        fields = ['id', 'file', 'uploaded_at']

class CaseSerializer(serializers.ModelSerializer):
    # রিড-অনলি ফিল্ডস (রেসপন্স এর জন্য)
    documents = CaseDocumentSerializer(many=True, read_only=True)
    case_type_details = CaseTypeSerializer(source='case_type', read_only=True)
    
    # রাইটেবল ফিল্ড (ইনপুট এর জন্য)
    case_type = serializers.PrimaryKeyRelatedField(
        queryset=CaseType.objects.all(), 
        required=True
    )

    class Meta:
        model = ImmigrationCase
        fields = [
            'id', 'case_number', 'case_type', 'case_type_details', 'title', 
            'last_update', 'status', 'reminder_date', 'reminder_note', 
            'notes', 'documents', 'created_at'
        ]

    def create(self, validated_data):
        # রিকোয়েস্ট থেকে ইউজার সেট করা
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def to_representation(self, instance):
        # আউটপুটে যদি case_type না থাকে তবে যেন এরর না দেয় তার হ্যান্ডলিং
        representation = super().to_representation(instance)
        if not instance.case_type:
            representation['case_type_details'] = None
        return representation