from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        (1, 'student'),
        (2, 'teacher'),
        (3, 'admin'),
    )
    user_type = models.PositiveSmallIntegerField(choices=USER_TYPE_CHOICES)

    # Add related_name to avoid clashes
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="custom_user_set",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="custom_user_set",
        related_query_name="user",
    )


class Semester(models.Model):
    name = models.CharField(max_length=20)  # e.g., "Fall 2023"
    start_date = models.DateField()
    end_date = models.DateField()
    course_registration_start = models.DateTimeField()
    course_registration_end = models.DateTimeField()
    add_and_drop_start = models.DateTimeField()
    add_and_drop_end = models.DateTimeField()


class Course(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    credits = models.PositiveIntegerField()
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='courses_taught')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='courses')


class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    midterm_grade = models.FloatField(null=True, blank=True)
    final_grade = models.FloatField(null=True, blank=True)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
