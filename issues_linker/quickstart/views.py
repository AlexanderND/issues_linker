#from django.contrib.auth.models import User, Group
from rest_framework import viewsets

# мои модели (хранение на сервере)
from issues_linker.quickstart.serializers import Payload_GH_Serializer, Payload_RM_Serializer
from issues_linker.quickstart.models import Payload_GH, Payload_RM

# мои модели (связь)
from issues_linker.quickstart.models import Linked_Projects, Linked_Issues, Linked_Comments
from issues_linker.quickstart.serializers import Linked_Projects_Serializer, Linked_Issues_Serializer, Linked_Comments_Serializer

# мои модели (очередь обработки задач)
from issues_linker.quickstart.serializers import Tasks_In_Queue_Serializer
from issues_linker.quickstart.models_tasks_queue import Tasks_In_Queue, Tasks_In_Queue_Manager
from issues_linker.quickstart.models_tasks_queue import put_task_in_queue

from django.http import HttpResponse    # ответы серверу

from issues_linker.my_functions import WRITE_LOG_ERR    # ведение логов ошибок
from issues_linker.my_functions import WRITE_LOG        # ведение логов
import json

from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404, redirect

import os

'''# testing
class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer'''


def standard_server_response(sender):

    response_text = 'The issues_linker server has successfully received the payload from ' + sender
    response = HttpResponse(response_text, status=200)

    return response


# ================================================ ОЧЕРЕДЬ ОБРАБОТКИ ЗАДАЧ =============================================


''' задача в очереди обработки задач '''
class Tasks_In_Queue_ViewSet(viewsets.ModelViewSet):
    '''
    Tasks_In_Queue_ViewSet.\n
    Здесь хранится информация о том, какие задачи ожидают обработку\n
    '''
    
    queryset = Tasks_In_Queue.objects.all()
    serializer_class = Tasks_In_Queue_Serializer


# ======================================================= GITHUB =======================================================


''' payloads от гитхаба '''
class Payload_From_GH_ViewSet(viewsets.ModelViewSet):
    """
    Payload_From_GH_ViewSet.\n
    Сюда приходят Payloads с гитхаба.\n
    Затем, они отправляются на редмайн.
    """
    queryset = Payload_GH.objects.all()
    serializer_class = Payload_GH_Serializer

    # переопределение create, чтобы сразу отправлять загруженные issue на RM
    def create(self, request, *args, **kwargs):
        payload = request.data
        put_task_in_queue(payload, 3)    # добавление задачи в очередь на обработку
        return standard_server_response('Github')

''' payloads от гитхаба (комментарии) '''
class Comment_Payload_From_GH_ViewSet(viewsets.ModelViewSet):
    """
    Comment_Payload_From_GH_ViewSet.\n
    Сюда приходят Payloads с гитхаба (комментарии).\n
    Затем, они отправляются на редмайн.
    """
    queryset = Payload_GH.objects.all()
    serializer_class = Payload_GH_Serializer

    # переопределение create, чтобы сразу отправлять загруженные issue на RM
    def create(self, request, *args, **kwargs):
        payload = request.data
        put_task_in_queue(payload, 4)    # добавление задачи в очередь на обработку
        return standard_server_response('Github')


# ======================================================= REDMINE ======================================================


''' payloads от редмайна '''
class Payload_From_RM_ViewSet(viewsets.ModelViewSet):
    """
    Payload_From_RM_ViewSet.\n
    Сюда приходят Payloads с редмайна.\n
    Затем, они отправляются на гитхаб.
    """

    queryset = Payload_RM.objects.all()
    serializer_class = Payload_RM_Serializer

    # переопределение create, чтобы сразу отправлять загруженные issue на GH
    def create(self, request, *args, **kwargs):
        payload = request.data
        put_task_in_queue(payload, 2)    # добавление задачи в очередь на обработку
        return standard_server_response('Redmine')


# ======================================================== СВЯЗЬ =======================================================


''' связынные комментарии в issue'''
class Linked_Comments_ViewSet(viewsets.ModelViewSet):
    """
    Linked_Comments_ViewSet.
    Здесь хранится информация о том, какие комментарии связаны между собой.
    """
    queryset = Linked_Comments.objects.all()
    serializer_class = Linked_Comments_Serializer

''' связынные issues в проекте '''
class Linked_Issues_ViewSet(viewsets.ModelViewSet):
    """
    Linked_Issues_ViewSet.
    Здесь хранится информация о том, какие issue связаны между собой.
    """
    queryset = Linked_Issues.objects.all()
    serializer_class = Linked_Issues_Serializer

''' связынные проекты '''
class Linked_Projects_ViewSet(viewsets.ModelViewSet):
    """
    Linked_Projects_ViewSet.\n
    Здесь хранится информация о том, какие проекты связаны между собой.\n
    """

    # переопределение create, чтобы получить id проектов из ссылок
    def create(self, request, *args, **kwargs):

        payload = json.dumps(request.data)  # превращаем QueryDict в JSON - сериализуемую строку
        payload = json.loads(payload)       # превращаем payload в JSON

        put_task_in_queue(payload, 1)       # добавление задачи в очередь на обработку

        server_response = 'you. Check the server logs for more detailed information.'
        return standard_server_response(server_response)

    queryset = Linked_Projects.objects.all()
    serializer_class = Linked_Projects_Serializer


# ================================================= ФОРМА СВЯЗИ ПРОЕКТОВ ===============================================


class Linked_Projects_List(APIView):

    renderer_classes = [TemplateHTMLRenderer]

    script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
    template_name = os.path.join(script_dir, 'data/linked_projects_list.html')


    def get(self, request):
        queryset = Linked_Projects.objects.all()
        return Response({'linked_projects': queryset})

class Linked_Project_Detail(APIView):

    renderer_classes = [TemplateHTMLRenderer]

    script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
    template_name = os.path.join(script_dir, 'data/linked_project_detail.html')


    def get(self, request, pk):
        linked_project = get_object_or_404(Linked_Projects, pk=pk)
        serializer = Linked_Projects_Serializer(linked_project)
        return Response({'serializer': serializer, 'profile': linked_project})

    def post(self, request, pk):
        linked_project = get_object_or_404(Linked_Projects, pk=pk)
        serializer = Linked_Projects_Serializer(linked_project, data=request.data)
        if not serializer.is_valid():
            return Response({'serializer': serializer, 'linked_project': linked_project})
        serializer.save()
        return redirect('linked_projects_list')
