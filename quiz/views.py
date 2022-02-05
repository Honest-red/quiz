from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import reverse
from django.views.generic import CreateView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView

from .forms import ChoicesFormSet
from .models import Exam
from .models import Question
from .models import Result


class ExamListView(LoginRequiredMixin, ListView):
    model = Exam
    template_name = 'exams/list.html'
    context_object_name = 'exams'


class ExamDetailView(LoginRequiredMixin, DetailView):
    model = Exam
    template_name = 'exams/details.html'
    context_object_name = 'exam'
    pk_url_kwarg = 'uuid'

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return self.model.objects.get(uuid=uuid)


class ExamResultCreateView(LoginRequiredMixin, CreateView):
    def post(self, request, *args, **kwargs):
        uuid = kwargs.get('uuid')
        result = Result.objects.create(
            user=request.user,
            exam=Exam.objects.get(uuid=uuid),
            state=Result.STATE.NEW
        )
        result.save()

        return HttpResponseRedirect(
            reverse(
                'quizzes:question',
                kwargs={
                    'uuid': uuid,
                    'res_uuid': result.uuid,
                    'order_num': 1
                }
            )
        )


class ExamResultQuestionView(LoginRequiredMixin, UpdateView):
    def get(self, request, *args, **kwargs):
        uuid = kwargs.get('uuid')
        order_num = kwargs.get('order_num')
        question = Question.objects.get(
            exam__uuid=uuid,
            order_num=order_num
        )

        choices = ChoicesFormSet(queryset=question.choices.all())

        return render(request, 'exams/question.html', context={'question': question, 'choices': choices})

    def post(self, request, *args, **kwargs):
        uuid = kwargs.get('uuid')
        res_uuid = kwargs.get('res_uuid')
        order_num = kwargs.get('order_num')
        question = Question.objects.get(
            exam__uuid=uuid,
            order_num=order_num
        )
        choices = ChoicesFormSet(data=request.POST)
        selected_choices = ['is_selected' in form.changed_data for form in choices.forms]
        result = Result.objects.get(uuid=res_uuid)
        result.update_result(order_num, question, selected_choices)

        if result.state == Result.STATE.FINISHED:
            return HttpResponseRedirect(
                reverse(
                    'quizzes:result_details',
                    kwargs={
                        'uuid': uuid,
                        'res_uuid': result.uuid
                    }
                )
            )
        return HttpResponseRedirect(
            reverse(
                'quizzes:question',
                kwargs={
                    'uuid': uuid,
                    'res_uuid': res_uuid,
                    'order_num': order_num + 1
                }
            )
        )


class ExamResultDetailView(LoginRequiredMixin, DetailView):
    model = Result
    template_name = 'results/details.html'
    context_object_name = 'result'
    pk_url_kwarg = 'uuid'

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('res_uuid')
        return self.get_queryset().get(uuid=uuid)
