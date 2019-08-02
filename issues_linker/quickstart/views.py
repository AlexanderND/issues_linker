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
#from issues_linker.quickstart.serializers import Queue_Serializer
#from issues_linker.quickstart.models import Queue

# обработка payload-ов
from issues_linker.process_payload_from_gh import process_payload_from_gh    # загрузка issue в Redmine
from issues_linker.process_payload_from_rm import process_payload_from_rm    # загрузка issue в Github

# загрузка комментариев к issue в Github
from issues_linker.process_comment_payload_from_gh import process_comment_payload_from_gh

# связь проектов
from issues_linker.link_projects import link_projects


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

        #queue = Queue.load()                                # загрузка очереди
        #queue.get_in_line(3)     # добавление задачи в очередь

        process_result = process_payload_from_gh(request.data)

        #queue.get_out_of_line()                             # удаление задачи из очереди

        #return super(Payload_From_GH_ViewSet, self).create(request, *args, **kwargs)
        return process_result

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

        #queue = Queue.load()                                # загрузка очереди
        #queue.get_in_line(4)     # добавление задачи в очередь

        process_result = process_comment_payload_from_gh(request.data)

        #queue.get_out_of_line()                             # удаление задачи из очереди

        #return super(Comment_Payload_From_GH_ViewSet, self).create(request, *args, **kwargs)
        return process_result


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

        #queue = Queue.load()        # загрузка очереди
        #queue.get_in_line(2)        # добавление задачи в очередь

        process_result = process_payload_from_rm(request.data)

        #queue.get_out_of_line()     # удаление задачи из очереди

        #return super(Payload_From_RM_ViewSet, self).create(request, *args, **kwargs)
        return process_result


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

        #queue = Queue.load()                        # загрузка очереди
        #queue.get_in_line(1)                        # добавление задачи в очередь

        link_result = link_projects(request.data)   # обработка запроса

        #queue.get_out_of_line()                     # удаление задачи из очереди

        #return super(Linked_Projects_ViewSet, self).create(request, *args, **kwargs)
        return link_result

    queryset = Linked_Projects.objects.all()
    serializer_class = Linked_Projects_Serializer


# ================================================ ОЧЕРЕДЬ ОБРАБОТКИ ЗАДАЧ =============================================


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
'''class Queue_ViewSet(viewsets.ModelViewSet):
    """
    Queue_ViewSet.\n
    Здесь хранится информация о том, какие проекты задачи ожидают обработку\n
    """

    # переопределение create
    def create(self, request, *args, **kwargs):
        return 'no'

    queryset = Queue.objects.all()
    serializer_class = Queue_Serializer'''
