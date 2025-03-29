# from django.contrib import admin
# from .models import Batch, Branch, Student, Semester, Subject, Mark

# @admin.register(Batch)
# class BatchAdmin(admin.ModelAdmin):
#     list_display = ('year',)

# @admin.register(Branch)
# class BranchAdmin(admin.ModelAdmin):
#     list_display = ('code', 'name')

# @admin.register(Student)
# class StudentAdmin(admin.ModelAdmin):
#     list_display = ('usn', 'name', 'branch', 'batch_year')

# @admin.register(Semester)
# class SemesterAdmin(admin.ModelAdmin):
#     list_display = ('number', 'branch')

# @admin.register(Subject)
# class SubjectAdmin(admin.ModelAdmin):
#     list_display = ('code', 'name', 'semester')

# @admin.register(Mark)
# class MarkAdmin(admin.ModelAdmin):
#     list_display = ('student', 'subject', 'marks_obtained', 'grade', 'academic_year')