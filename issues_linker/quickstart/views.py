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
import datetime

from issues_linker.my_functions import allowed_ips, secret_gh

import hmac
#import OpenSSL
#from hashlib import sha1
import hashlib


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

def error_server_response(error_text, status_code):

    WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
              error_text + '\n')

    response = HttpResponse(error_text, status=status_code)

    return response


def chk_if_ip_is_allowed(ip):

    for allowed_ip in allowed_ips:

        if(ip == allowed_ip):
            return True

    return False

def chk_if_secret_is_valid(secret, payload_body):

    '''secret_encoded = bytearray(secret, encoding='utf8')
    #payload_body_encoded = bytearray(str(payload_body), encoding='utf8')
    payload_body_encoded = bytearray(json.dumps(payload_body), encoding='utf8')'''


    '''signature = 'sha1=' + OpenSSL::HMAC.hexdigest(OpenSSL::Digest.new('sha1'), bytearray(secret_gh, encoding='utf8'), payload_body_encoded)'''
    #sha = sha1(payload_body_encoded)
    #sha.update(bytearray(secret_gh, encoding='utf8'))
    #sha = sha1(bytearray(secret_gh, encoding='utf8'))
    #sha.update(payload_body_encoded)

    #signature = 'sha1=' + str(sha.hexdigest())
    #signature = sha.hexdigest()

    '''signature = hmac.new(
        secret_gh.encode(),
        json.dumps(payload_body, separators=(',', ':')).encode(),
        sha1
    ).hexdigest()'''

    secret_gh_encoded = secret_gh.encode(secret_gh)
    payload_body_encoded = json.dumps(payload_body)
    payload_body_encoded = payload_body_encoded.encode()

    signature = hashlib.sha1(secret_gh)
    #signature.update(secret_gh_encoded)
    #signature.update(payload_body_encoded)
    signature = signature.hexdigest()
    """signature = hmac.new(secret_gh_encoded,
                         msg=payload_body_encoded,
                         digestmod=hashlib.sha1
                         ).hexdigest()"""

    signature = 'sha1=' + signature

    WRITE_LOG('\nsecret_gh:')
    WRITE_LOG(str(secret_gh))

    WRITE_LOG('\nsecret:')
    WRITE_LOG(str(secret))

    WRITE_LOG('\nsignature:')
    WRITE_LOG(signature)

    if(secret == signature):
        return True

    return False


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

        """
        try:
            # проверка секрета гитхаба
            secret_gh = request.META['HTTP_X_HUB_SIGNATURE']
            if(not chk_if_secret_is_valid(secret_gh, request.data)):

                error_text = "ERROR: received POST request: payloads_from_gh\n" +\
                             "But the HTTP_X_HUB_SIGNATURE doesn't match the secret_gh\n" +\
                             "HTTP_X_HUB_SIGNATURE: " + secret_gh + "\n"
                return error_server_response(error_text, 401)

        except:

            error_text = "ERROR: received POST request: payloads_from_gh\n" +\
                         "But the request doesn't have the 'HTTP_X_HUB_SIGNATURE' header"
            return error_server_response(error_text, 400)
        """

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

        """
        try:
            # проверка секрета гитхаба
            secret_gh = request.META['HTTP_X_HUB_SIGNATURE']
            if(not chk_if_secret_is_valid(secret_gh, request.data)):

                error_text = "ERROR: received POST request: comment_payloads_from_gh\n" +\
                             "But the HTTP_X_HUB_SIGNATURE doesn't match the secret_gh\n" +\
                             "HTTP_X_HUB_SIGNATURE: " + secret_gh + "\n"
                return error_server_response(error_text, 401)

        except:

            error_text = "ERROR: received POST request: comment_payloads_from_gh\n" +\
                         "But the request doesn't have the 'HTTP_X_HUB_SIGNATURE' header"
            return error_server_response(error_text, 400)
        """

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

        try:
            # проверка, что с данного ip разрешено принимать POST запросы
            sender_ip = request.META['REMOTE_ADDR']
            if(not chk_if_ip_is_allowed(sender_ip)):

                error_text = "ERROR: received POST request: payloads_from_rm\n" +\
                             "But the sender_ip doesn't match any of the allowed_ips\n" +\
                             "sender_ip: " + sender_ip + "\n"
                return error_server_response(error_text, 401)

        except:

            error_text = "ERROR: received POST request: payloads_from_rm\n" +\
                         "But the request doesn't have the 'REMOTE_ADDR' header"
            return error_server_response(error_text, 400)

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

        try:
            # проверка, что с данного ip разрешено принимать POST запросы
            sender_ip = request.META['REMOTE_ADDR']
            if(not chk_if_ip_is_allowed(sender_ip)):

                error_text = "ERROR: received POST request: linked_projects\n" +\
                             "But the sender_ip doesn't match any of the allowed_ips\n" +\
                             "sender_ip: " + sender_ip + "\n"
                return error_server_response(error_text, 401)

        except:

            error_text = "ERROR: received POST request: linked_projects\n" +\
                         "But the request doesn't have the 'REMOTE_ADDR' header"
            return error_server_response(error_text, 400)

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
