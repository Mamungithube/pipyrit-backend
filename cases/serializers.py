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

    documents = CaseDocumentSerializer(many=True, read_only=True)
    case_type_details = CaseTypeSerializer(source='case_type', read_only=True)
    
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

        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if not instance.case_type:
            representation['case_type_details'] = None
        return representation