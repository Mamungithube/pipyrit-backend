from rest_framework import viewsets, status, generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_yasg.utils import swagger_auto_schema
from .models import ImmigrationCase, CaseType, CaseDocument
from .serializers import CaseSerializer, CaseTypeSerializer
from user.views import api_response 

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
        if getattr(self, 'swagger_fake_view', False):
            return ImmigrationCase.objects.none()
            
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
            files = request.FILES.getlist('documents')
            for f in files:
                CaseDocument.objects.create(case=case_instance, file=f)
            return api_response(True, "Case created successfully", serializer.data, status.HTTP_201_CREATED)
        
        error_msg = list(serializer.errors.values())[0][0]
        return api_response(False, error_msg if isinstance(error_msg, str) else error_msg[0], serializer.errors, status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=['3. Case Management'])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_response(True, "Case details fetched", serializer.data)

    @swagger_auto_schema(tags=['3. Case Management'])
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(tags=['3. Case Management'])
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            case_instance = serializer.save()
            
            # ১. নতুন ফাইল আসছে কি না চেক করা
            files = request.FILES.getlist('documents')
            
            if files:
                # ২. ফিক্স: যদি নতুন ফাইল আপলোড করা হয়, তবে পুরানো সব ফাইল মুছে ফেলো
                case_instance.documents.all().delete() 
                
                # ৩. এখন নতুন ফাইলগুলো সেভ করো
                for f in files:
                    CaseDocument.objects.create(case=case_instance, file=f)
            
            return api_response(True, "Case updated successfully", serializer.data)
        
        return api_response(False, "Update failed", serializer.errors, status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=['3. Case Management'])
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return api_response(True, "Case deleted successfully", None, status.HTTP_204_NO_CONTENT)
    

class AdminCaseTypeViewSet(viewsets.ModelViewSet):
    queryset = CaseType.objects.all().order_by('name')
    serializer_class = CaseTypeSerializer
    permission_classes = [IsAdminUser] 


    @swagger_auto_schema(tags=['Admin  Case Type Management'])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


    @swagger_auto_schema(tags=['Admin  Case Type Management'])
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(tags=['Admin  Case Type Management'])
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return api_response(True, "All case types fetched", serializer.data)

    @swagger_auto_schema(tags=['Admin  Case Type Management'])
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return api_response(True, "Case type added successfully", serializer.data, status.HTTP_201_CREATED)
        return api_response(False, "Failed to add case type", serializer.errors, status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=['Admin  Case Type Management'])
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return api_response(True, "Case type updated successfully", serializer.data)
        return api_response(False, "Update failed", serializer.errors, status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=['Admin  Case Type Management'])
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return api_response(True, "Case type deleted successfully", None, status.HTTP_204_NO_CONTENT)