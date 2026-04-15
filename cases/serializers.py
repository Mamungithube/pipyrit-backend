from rest_framework import serializers
from .models import ImmigrationCase, CaseType, CaseDocument

class CaseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseType
        fields = '__all__'

class CaseDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseDocument
        fields = ['id', 'file', 'uploaded_at']

class CaseSerializer(serializers.ModelSerializer):
    documents = CaseDocumentSerializer(many=True, read_only=True)
    case_type_name = serializers.ReadOnlyField(source='case_type.name')

    class Meta:
        model = ImmigrationCase
        fields = [
            'id', 'case_number', 'case_type', 'case_type_name', 'title', 
            'last_update', 'status', 'reminder_date', 'reminder_note', 
            'notes', 'documents', 'created_at'
        ]

    def create(self, validated_data):
        # অটোমেটিক কারেন্ট ইউজার সেট করার জন্য
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)