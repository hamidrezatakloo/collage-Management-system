from django.core.exceptions import ValidationError
from django.utils import timezone


class Enrollment:
    @staticmethod
    def validate_enrollment_create(student, course, enrollments):
        if student.user_type != 1:  # Ensure only students can enroll
            raise ValidationError("Only students can enroll in courses.")

        # Check if within registration period
        now = timezone.now()
        semester = course.semester
        if Enrollment.can_register(semester) or Enrollment.can_add_drop_course(semester):
            raise ValidationError("Course registration is not currently open.")

        # Check if student has reached the 20 unit limit
        student_credits = sum(enrollment.course.credits for enrollment in enrollments)
        if student_credits + course.credits > 20:
            raise ValidationError("Students can only enroll in up to 20 credits per semester.")

    @staticmethod
    def validate_enrollment_destroy(course):
        # Check if within registration period
        semester = course.semester
        if Enrollment.can_register(semester) or Enrollment.can_add_drop_course(semester):
            raise ValidationError("Course registration is not currently open.")

    @staticmethod
    def can_register(semester):
        now = timezone.now()
        return semester.course_registration_start <= now <= semester.course_registration_end

    @staticmethod
    def can_add_drop_course(semester):
        now = timezone.now()
        return semester.add_and_drop_start <= now <= semester.add_and_drop_end
