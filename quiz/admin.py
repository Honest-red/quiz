from django.contrib import admin

from .models import Choice
from .models import Exam
from .models import Question
from .models import Result


class ListChoice(admin.ModelAdmin):
    list_display = [
        'question',
        'text',
        'is_correct'
        ]


admin.site.register(Exam)
admin.site.register(Question)
admin.site.register(Choice, ListChoice)
admin.site.register(Result)


