# from django.db import models
# import uuid


# class Batch(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     year = models.CharField(max_length=4)
    
#     def __str__(self):
#         return self.year


# class Branch(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     code = models.CharField(max_length=2)
#     name = models.CharField(max_length=100)
    

#     CODE_TO_NAME_MAP = {
#         'CS': 'Computer Science & Engineering',
#         'EE': 'Electrical & Electronics Engineering',
#         'ME': 'Mechanical Engineering',
#         'CV': 'Civil Engineering',
#         'AD': 'Artificial Intelligence & Data Science',
#         'EC': 'Electronics & Communication Engineering',
#     }

#     def save(self, *args, **kwargs):
#         if not self.name and self.code in self.CODE_TO_NAME_MAP:
#             self.name = self.CODE_TO_NAME_MAP[self.code]
#         super(Branch, self).save(*args, **kwargs)
#     def __str__(self):
#         return self.name


# class Student(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     name = models.CharField(max_length=100)
#     usn = models.CharField(max_length=10, unique=True)
#     branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='students')
#     batch_year = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='students')
    
#     class Meta:
#         indexes = [
#             models.Index(fields=['branch', 'batch_year']),
#         ]
    
#     def __str__(self):
#         return f"{self.name} ({self.usn})"


# class Semester(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     number = models.IntegerField()
#     branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='semesters')
    
#     class Meta:
#         unique_together = ['number', 'branch']
    
#     def __str__(self):
#         return f"Semester {self.number} - {self.branch.name}"


# class Subject(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     name = models.CharField(max_length=100)
#     code = models.CharField(max_length=10)
#     semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='subjects')
    
#     class Meta:
#         unique_together = ['code', 'semester']
    
#     def __str__(self):
#         return f"{self.code} - {self.name}"


# class Mark(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='marks')
#     subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='marks')
#     marks_obtained = models.IntegerField()
#     grade = models.CharField(max_length=2, blank=True, null=True)
#     academic_year = models.CharField(max_length=9)
    
#     class Meta:
#         unique_together = ['student', 'subject', 'academic_year']
    
#     def __str__(self):
#         return f"{self.student.name} - {self.subject.name}: {self.marks_obtained}"
    