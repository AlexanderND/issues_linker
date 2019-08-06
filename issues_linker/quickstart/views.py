#from django.contrib.auth.models import User, Group
from rest_framework import viewsets

# мои модели (хранение на сервере)
from issues_linker.quickstart.serializers import Payload_GH_Serializer, Payload_RM_Serializer
from issues_linker.quickstart.models import Payload_GH, Payload_RM

# мои модели (связь)
from issues_linker.quickstart.models import Linked_Projects, Linked_Issues, Linked_Comments
from issues_linker.quickstart.serializers import Linked_Projects_Serializer, Linked_Issues_Serializer, Linked_Comments_Serializer

# мои модели (очередь обработки задач)
#from issues_linker.quickstart.serializers import Tasks_In_Queue_Serializer, Queue_Serializer
#from issues_linker.quickstart.models import Tasks_In_Queue, Queue
#from issues_linker.quickstart.serializers import Tasks_Queue_Serializer
#from issues_linker.quickstart.models import Tasks_Queue

# обработка payload-ов
from issues_linker.process_payload_from_gh import process_payload_from_gh    # загрузка issue в Redmine
from issues_linker.process_payload_from_rm import process_payload_from_rm    # загрузка issue в Github

# загрузка комментариев к issue в Github
from issues_linker.process_comment_payload_from_gh import process_comment_payload_from_gh

from django.http import HttpResponse    # ответы серверу

# связь проектов
from issues_linker.link_projects import link_projects

# очередь задач
from issues_linker.settings import tasks_queue          # очередь обработки задач
from multiprocessing import Process                     # многопроцессорность
import threading                                        # многопоточность
import time

from issues_linker.my_functions import WRITE_LOG_ERR                # ведение логов ошибок

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


class Task_In_Queue():

    def __init__(self, payload, type):

        self.payload = payload

        ''' 1 - link_projects '''
        ''' 2 - process_payload_from_rm '''
        ''' 3 - process_payload_from_gh '''
        ''' 4 - process_comment_payload_from_gh '''
        self.type = type

def process_payload(payload, type):

    # определяем тип обработки
    if (type == 1):
        process_result = link_projects(payload)

    elif (type == 2):
        process_result = process_payload_from_rm(payload)

    elif (type == 3):
        process_result = process_payload_from_gh(payload)

    else:  # type == 4
        process_result = process_comment_payload_from_gh(payload)

    return process_result

def tasks_queue_daemon(sleep_retry):
    retry_wait = 0

    # продолжаем брать задачи из очереди, пока есть задачи
    while (len(tasks_queue) > 0):

        payload = tasks_queue[0].payload
        type = tasks_queue[0].type

        try:
            process_result = process_payload(payload, type)

            # определяем результат обработки
            if (process_result.status_code == 200 or process_result.status_code == 201):
                retry_wait = 0              # сброс времени ожидания перед повторным запуском
                tasks_queue.popleft()       # удаляем задачу из очереди

            else:
                retry_wait += sleep_retry   # увеличение времени ожидания (чтобы не перегружать сервер)
        except:
            retry_wait += sleep_retry       # увеличение времени ожидания (чтобы не перегружать сервер)
            pass

        time.sleep(retry_wait)              # ждём перед следующим запуском

def put_in_queue(payload, type):

    # создаём задачу на обработку
    task_in_queue = Task_In_Queue(payload, type)
    tasks_queue.append(task_in_queue)   # добавляем задачу в очередь обработки

    # запускаем демона, отчищающего очередь, если в очереди только 1 элемент (только что добавили)
    if (len(tasks_queue) == 1):

        sleep_retry = 2
        daemon = threading.Thread(target=tasks_queue_daemon,
                             args=(sleep_retry,),
                             daemon=True)
        daemon.start()


''' задачи в очереди обработки задач '''
'''class Tasks_In_Queue_ViewSet(viewsets.ModelViewSet):
    """
    Tasks_In_Queue_ViewSet.\n
    Здесь хранится информация о том, какие проекты задачи ожидают обработку\n
    """

    # переопределение create
    def create(self, request, *args, **kwargs):
        return 'no'

    queryset = Tasks_In_Queue.objects.all()
    serializer_class = Tasks_In_Queue_Serializer'''

''' очередь обработки задач '''
'''class Tasks_Queue_ViewSet(viewsets.ModelViewSet):
    """
    Queue_ViewSet.\n
    Здесь хранится информация о том, какие проекты задачи ожидают обработку\n
    """

    # переопределение create
    def create(self, request, *args, **kwargs):
        return 'no'

    queryset = Tasks_Queue.objects.all()
    serializer_class = Tasks_Queue_Serializer'''


# ======================================================= GITHUB =======================================================


# TODO: добавлять в очередь
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
        put_in_queue(payload, 3)    # добавление задачи в очередь на обработку
        return standard_server_response('Github')

# TODO: добавлять в очередь
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
        put_in_queue(payload, 4)    # добавление задачи в очередь на обработку
        return standard_server_response('Github')


# ======================================================= REDMINE ======================================================


# TODO: добавлять в очередь
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
        put_in_queue(payload, 2)    # добавление задачи в очередь на обработку
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
    Пожалуйста, используйте или ссылки, или id (иначе всё может сломаться).\n
    Максимальная длина url_rm: 256\n
    Максимальная длина url_gh: 256\n
    """

    # переопределение create, чтобы получить id проектов из ссылок
    def create(self, request, *args, **kwargs):
        payload = request.data
        put_in_queue(payload, 1)       # добавление задачи в очередь на обработку
        return standard_server_response('YOU')

    queryset = Linked_Projects.objects.all()
    serializer_class = Linked_Projects_Serializer
