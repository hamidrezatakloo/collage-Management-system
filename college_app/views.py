from rest_framework import viewsets, permissions, status, generics
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from .models import User, Course, Enrollment, Semester
from .serializers import UserSerializer, CourseSerializer, EnrollmentSerializer, SemesterSerializer
from services.college_app import Enrollment as EnrollmentValidation


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.user_type == 3


class IsTeacherUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.user_type == 2


class IsStudentUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.user_type == 1


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsTeacherUser | IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]


class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer

    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            permission_classes = [IsStudentUser]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsTeacherUser | IsAdminUser]
        elif self.action in ['my_courses']:
            permission_classes = [IsStudentUser]
        elif self.action in ['my_students']:
            permission_classes = [IsTeacherUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        student = request.user
        course = Course.objects.get(id=request.data['course'])
        enrollments = Enrollment.objects.filter(student=student, course__semester=course.semester)

        try:
            EnrollmentValidation.validate_enrollment_create(student, course, enrollments)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        enrollment = self.get_object()
        try:
            EnrollmentValidation.validate_enrollment_destroy(enrollment.course)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'], permission_classes=[IsStudentUser])
    def my_courses(self, request):
        enrollments = Enrollment.objects.filter(student=request.user)
        serializer = self.get_serializer(enrollments, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsTeacherUser])
    def my_students(self, request):
        courses = Course.objects.filter(teacher=request.user)
        enrollments = Enrollment.objects.filter(course__in=courses)
        serializer = self.get_serializer(enrollments, many=True)
        return Response(serializer.data)


class SemesterViewSet(viewsets.ModelViewSet):
    queryset = Semester.objects.all()
    serializer_class = SemesterSerializer
    permission_classes = [IsAdminUser]


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserSerializer


class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'user_type': user.user_type
        })
