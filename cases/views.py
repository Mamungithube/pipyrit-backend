from rest_framework import viewsets, status, generics
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from .models import ImmigrationCase, CaseType, CaseDocument
from .serializers import CaseSerializer, CaseTypeSerializer
from user.views import api_response # আগের অ্যাপ থেকে ইম্পোর্ট

class CaseTypeListView(generics.ListAPIView):
    queryset = CaseType.objects.all()
    serializer_class = CaseTypeSerializer
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(tags=['3. Case Management'])
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return api_response(True, "Case types fetched", serializer.data)

class CaseViewSet(viewsets.ModelViewSet):
    serializer_class = CaseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # ইউজার শুধুমাত্র তার নিজের কেসগুলো দেখবে
        return ImmigrationCase.objects.filter(user=self.request.user).order_by('-created_at')

    @swagger_auto_schema(tags=['3. Case Management'])
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return api_response(True, "Cases retrieved successfully", serializer.data)

    @swagger_auto_schema(tags=['3. Case Management'])
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            case_instance = serializer.save()
            
            # মাল্টিপল ডকুমেন্ট হ্যান্ডেল করা (যদি থাকে)
            files = request.FILES.getlist('documents')
            for f in files:
                CaseDocument.objects.create(case=case_instance, file=f)
            
            return api_response(True, "Case created successfully", serializer.data, status.HTTP_201_CREATED)
        
        error_msg = list(serializer.errors.values())[0][0]
        return api_response(False, error_msg, serializer.errors, status.HTTP_300_BAD_REQUEST)

    @swagger_auto_schema(tags=['3. Case Management'])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_response(True, "Case details fetched", serializer.data)