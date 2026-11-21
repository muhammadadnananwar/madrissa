from rest_framework import serializers

from core.serializers import LabeledModelSerializer

from .models import (Assignment, AttemptAnswer, Choice, Course, CourseEnrollment, DiscussionReply, DiscussionThread,
                     Homework, Lesson, LessonProgress, Module, Question, Quiz, QuizAttempt, Submission)


class CourseSerializer(LabeledModelSerializer):
    class Meta:
        model = Course
        fields = "__all__"
        extra_kwargs = {"teacher": {"required": False}}


class CourseEnrollmentSerializer(LabeledModelSerializer):
    class Meta:
        model = CourseEnrollment
        fields = "__all__"


class ModuleSerializer(LabeledModelSerializer):
    class Meta:
        model = Module
        fields = "__all__"


class LessonSerializer(LabeledModelSerializer):
    class Meta:
        model = Lesson
        fields = "__all__"


class LessonProgressSerializer(LabeledModelSerializer):
    class Meta:
        model = LessonProgress
        fields = "__all__"


class AssignmentSerializer(LabeledModelSerializer):
    class Meta:
        model = Assignment
        fields = "__all__"


class SubmissionSerializer(LabeledModelSerializer):
    class Meta:
        model = Submission
        fields = "__all__"


class QuizSerializer(LabeledModelSerializer):
    class Meta:
        model = Quiz
        fields = "__all__"


class ChoiceSerializer(LabeledModelSerializer):
    class Meta:
        model = Choice
        fields = "__all__"


class QuestionSerializer(LabeledModelSerializer):
    class Meta:
        model = Question
        fields = "__all__"


class QuizAttemptSerializer(LabeledModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = "__all__"


class AttemptAnswerSerializer(LabeledModelSerializer):
    class Meta:
        model = AttemptAnswer
        fields = "__all__"


class DiscussionThreadSerializer(LabeledModelSerializer):
    class Meta:
        model = DiscussionThread
        fields = "__all__"


class DiscussionReplySerializer(LabeledModelSerializer):
    class Meta:
        model = DiscussionReply
        fields = "__all__"


class HomeworkSerializer(LabeledModelSerializer):
    class Meta:
        model = Homework
        fields = "__all__"


# ---- action payloads -------------------------------------------------------------
class SubmitAssignmentSerializer(serializers.Serializer):
    text = serializers.CharField(required=False, allow_blank=True, default="")
    file = serializers.FileField(required=False)


class GradeSubmissionSerializer(serializers.Serializer):
    marks = serializers.DecimalField(max_digits=6, decimal_places=2, min_value=0)
    feedback = serializers.CharField(required=False, allow_blank=True, default="")
    status = serializers.ChoiceField(choices=["graded", "returned"], default="graded")


class AnswerInputSerializer(serializers.Serializer):
    question = serializers.IntegerField()
    choices = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)
    text = serializers.CharField(required=False, allow_blank=True, default="")


class SubmitAttemptSerializer(serializers.Serializer):
    answers = AnswerInputSerializer(many=True)


class ManualGradeItemSerializer(serializers.Serializer):
    answer_id = serializers.IntegerField()
    marks = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=0)


class ManualGradeSerializer(serializers.Serializer):
    answers = ManualGradeItemSerializer(many=True)
