from django.contrib import admin

from .models import (Assignment, AttemptAnswer, Choice, Course, CourseEnrollment, DiscussionReply, DiscussionThread,
                     Homework, Lesson, LessonProgress, Module, Question, Quiz, QuizAttempt, Submission)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'code', 'subject', 'section', 'teacher', 'cover')
    search_fields = ('title', 'code')
    list_filter = ('enrollment_type', 'is_published', 'issue_certificate')
    list_select_related = ('subject', 'section', 'teacher')


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('course', 'student', 'completed', 'completed_at')
    list_filter = ('completed',)
    list_select_related = ('course', 'student')


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('course', 'title', 'order')
    search_fields = ('title',)
    list_select_related = ('course',)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('module', 'title', 'kind', 'media_url', 'file', 'duration_minutes')
    search_fields = ('title', 'media_url')
    list_filter = ('kind', 'is_published')
    list_select_related = ('module',)


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'student', 'completed', 'completed_at')
    list_filter = ('completed',)
    list_select_related = ('lesson', 'student')


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('course', 'title', 'attachment', 'due_at', 'max_marks', 'allow_late')
    search_fields = ('title',)
    list_filter = ('allow_late', 'is_published')
    list_select_related = ('course', 'created_by')


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'student', 'file', 'status', 'marks', 'graded_by')
    list_filter = ('status',)
    list_select_related = ('assignment', 'student', 'graded_by')


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('course', 'title', 'time_limit_minutes', 'max_attempts', 'pass_percentage', 'shuffle_questions')
    search_fields = ('title',)
    list_filter = ('shuffle_questions', 'show_answers', 'is_published')
    list_select_related = ('course',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'kind', 'marks', 'order')
    list_filter = ('kind',)
    list_select_related = ('quiz',)


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('question', 'text', 'is_correct')
    search_fields = ('text',)
    list_filter = ('is_correct',)
    list_select_related = ('question',)


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'student', 'started_at', 'submitted_at', 'status', 'score')
    list_filter = ('status', 'passed')
    list_select_related = ('quiz', 'student')


@admin.register(AttemptAnswer)
class AttemptAnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'is_correct', 'marks_awarded')
    list_filter = ('is_correct',)
    list_select_related = ('attempt', 'question')


@admin.register(DiscussionThread)
class DiscussionThreadAdmin(admin.ModelAdmin):
    list_display = ('course', 'title', 'author', 'is_pinned', 'is_locked')
    search_fields = ('title',)
    list_filter = ('is_pinned', 'is_locked')
    list_select_related = ('course', 'author')


@admin.register(DiscussionReply)
class DiscussionReplyAdmin(admin.ModelAdmin):
    list_display = ('thread', 'author')
    list_select_related = ('thread', 'author')


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ('section', 'subject', 'date', 'due_date', 'title', 'attachment')
    search_fields = ('title',)
    list_select_related = ('section', 'subject', 'created_by')
