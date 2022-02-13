from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import reverse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView
from django.views.generic.list import MultipleObjectMixin

from .forms import ChoicesFormSet
from .models import Exam
from .models import Question
from .models import Result


class ExamListView(LoginRequiredMixin, ListView):
    model = Exam
    template_name = 'exams/list.html'
    context_object_name = 'exams'


class ExamDetailView(LoginRequiredMixin, DetailView, MultipleObjectMixin):
    model = Exam
    template_name = 'exams/details.html'
    context_object_name = 'exam'
    pk_url_kwarg = 'uuid'
    paginate_by = 5

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return self.model.objects.get(uuid=uuid)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(object_list=self.get_queryset(), **kwargs)
        return context

    def get_queryset(self):
        return Result.objects.filter(
            exam=self.get_object(),
            user=self.request.user

        ).order_by('state')


class ExamResultCreateView(LoginRequiredMixin, CreateView):
    def post(self, request, *args, **kwargs):
        uuid = kwargs.get('uuid')
        result = Result.objects.create(
            user=request.user,
            exam=Exam.objects.get(uuid=uuid),
            state=Result.STATE.NEW,
            current_order_number=0
        )
        result.save()

        return HttpResponseRedirect(
            reverse(
                'quizzes:question',
                kwargs={
                    'uuid': uuid,
                    'res_uuid': result.uuid,

                }
            )
        )


class ExamResultQuestionView(LoginRequiredMixin, UpdateView):

    def __get_res_by_uuid(self, **kwargs):
        return Result.objects.get(uuid=kwargs.get('res_uuid'))

    def get(self, request, *args, **kwargs):
        uuid = kwargs.get('uuid')
        result = self.__get_res_by_uuid(**kwargs)
        question = Question.objects.get(
            exam__uuid=uuid,
            order_num=result.current_order_number + 1

        )

        choices = ChoicesFormSet(queryset=question.choices.all())

        return render(request, 'exams/question.html', context={'question': question, 'choices': choices})

    def post(self, request, *args, **kwargs):
        uuid = kwargs.get('uuid')
        res_uuid = kwargs.get('res_uuid')
        result = self.__get_res_by_uuid(**kwargs)
        question = Question.objects.get(
            exam__uuid=uuid,
            order_num=result.current_order_number + 1
        )
        choices = ChoicesFormSet(data=request.POST)
        selected_choices = ['is_selected' in form.changed_data for form in choices.forms]

        if sum(selected_choices) == 0:
            messages.warning(request, 'Not save if All answer not right')
        elif sum(selected_choices) == len(choices.forms):
            messages.warning(request, 'Not save if All answer right')
        else:
            result = Result.objects.get(uuid=res_uuid)
            result.update_result(result.current_order_number + 1, question, selected_choices)

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


class ExamResultUpdateView(LoginRequiredMixin, UpdateView):
    def get(self, request, *args, **kwargs):
        uuid = kwargs.get('uuid')
        res_uuid = kwargs.get('res_uuid')
        user = request.user

        result = Result.objects.get(
            user=user,
            uuid=res_uuid,
            exam__uuid=uuid
        )

        return HttpResponseRedirect(
            reverse(
                'quizzes:question',
                kwargs={
                    'uuid': uuid,
                    'res_uuid': result.uuid,

                }
            )
        )


class ExamResultDeleteView(LoginRequiredMixin, DeleteView):

    model = Result
    template_name = 'results/delete.html'
    context_object_name = 'result'
    pk_url_kwarg = 'uuid'
    success_url = reverse_lazy('quizzes:list')

    def get_object(self):
        uuid = self.kwargs.get('res_uuid')
        return self.get_queryset().get(uuid=uuid)

    def form_valid(self, request, *args, **kwargs):
        result = super().delete(request, *args, **kwargs)
        return result
