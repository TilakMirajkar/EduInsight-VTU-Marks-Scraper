import re
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_roll_number(value):
    """Validate USN format (e.g., 1AB21CS123)."""
    if not re.match(r"^\d{1}[A-Za-z]{2}\d{2}[A-Za-z]{2}\d{3}$", value):
        raise ValidationError(
            _("USN Error! Enter USN in the format: 1AB21CS123."),
            params={"value": value},
        )


class Batch(models.Model):
    batch = models.IntegerField(unique=True)

    def __str__(self):
        return f"Batch {self.batch}"


class Semester(models.Model):
    semester = models.IntegerField(unique=True, choices=((i, i) for i in range(1, 9)))

    def __str__(self):
        return f"Semester {self.semester}"


class Subject(models.Model):
    name = models.CharField(max_length=10)
    semester = models.ForeignKey(
        Semester, on_delete=models.CASCADE, related_name="subjects"
    )

    def __str__(self):
        return self.name


class Student(models.Model):
    name = models.CharField(max_length=100)
    usn = models.CharField(
        max_length=10, unique=True, validators=[validate_roll_number], db_index=True
    )
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="students")
    semester = models.ForeignKey(
        Semester,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
        default=1,
    )

    def __str__(self):
        return f"{self.name} ({self.usn})"


class Marks(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="marks")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="marks")
    semester = models.ForeignKey(
        Semester, on_delete=models.CASCADE, related_name="marks"
    )
    marks = models.IntegerField(default=0)

    class Meta:
        unique_together = ("student", "subject", "semester")

    def __str__(self):
        return f"{self.student.name} - {self.subject.name}: {self.marks}"