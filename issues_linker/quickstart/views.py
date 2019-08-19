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
import hashlib

# форма связи проектов
from issues_linker.quickstart.forms import Linked_Projects_Form

from django.shortcuts  import render


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

def chk_if_secret_gh_is_valid(request):

    secret_gh_encoded = bytearray(secret_gh, encoding='utf8')
    body_digest = hmac.new(secret_gh_encoded,
                           msg=request.body,
                           digestmod=hashlib.sha1
                           ).hexdigest()

    HTTP_X_HUB_SIGNATURE = request.META['HTTP_X_HUB_SIGNATURE']
    algorithm, signature_digest = HTTP_X_HUB_SIGNATURE.split('=')

    return hmac.compare_digest(body_digest, signature_digest)


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

        # проверка секрета гитхаба
        try:

            if(not chk_if_secret_gh_is_valid(request)):

                error_text = "ERROR: received POST request: payloads_from_gh\n" +\
                             "But the HTTP_X_HUB_SIGNATURE doesn't match the secret_gh\n" +\
                             "HTTP_X_HUB_SIGNATURE: " + secret_gh + "\n"
                return error_server_response(error_text, 401)

        except:

            error_text = "ERROR: received POST request: payloads_from_gh\n" +\
                         "Probably, the request doesn't have the 'HTTP_X_HUB_SIGNATURE' header\n"
            return error_server_response(error_text, 400)

        # определение event: issues, issue_comment
        try:

            payload = request.data

            HTTP_X_GITHUB_EVENT = request.META['HTTP_X_GITHUB_EVENT']

            if (HTTP_X_GITHUB_EVENT == 'issues'):

                put_task_in_queue(payload, 3)    # добавление задачи в очередь на обработку
                return standard_server_response('Github')

            elif (HTTP_X_GITHUB_EVENT == 'issue_comment'):

                put_task_in_queue(payload, 4)    # добавление задачи в очередь на обработку
                return standard_server_response('Github')

            else:

                error_text = "ERROR: received POST request: payloads_from_gh\n" +\
                             "But the HTTP_X_GITHUB_EVENT doesn't match any of the known HTTP_X_GITHUB_EVENT.\n" +\
                             "HTTP_X_GITHUB_EVENT: " + HTTP_X_GITHUB_EVENT + '\n' +\
                             'Allowed HTTP_X_GITHUB_EVENT: issues, issue_comment'
                return error_server_response(error_text, 401)

        except:

            error_text = "ERROR: received POST request: payloads_from_gh\n" +\
                         "Probably, the request doesn't have the 'HTTP_X_GITHUB_EVENT' header\n"
            return error_server_response(error_text, 401)

''' payloads от гитхаба (комментарии) '''
"""
class Comment_Payload_From_GH_ViewSet(viewsets.ModelViewSet):
    '''
    Comment_Payload_From_GH_ViewSet.\n
    Сюда приходят Payloads с гитхаба (комментарии).\n
    Затем, они отправляются на редмайн.
    '''
    queryset = Payload_GH.objects.all()
    serializer_class = Payload_GH_Serializer

    # переопределение create, чтобы сразу отправлять загруженные issue на RM
    def create(self, request, *args, **kwargs):

        # проверка секрета гитхаба
        try:
            if(not chk_if_secret_gh_is_valid(request)):

                error_text = "ERROR: received POST request: comment_payloads_from_gh\n" +\
                             "But the HTTP_X_HUB_SIGNATURE doesn't match the secret_gh\n" +\
                             "HTTP_X_HUB_SIGNATURE: " + secret_gh + "\n"
                return error_server_response(error_text, 401)

        except:

            error_text = "ERROR: received POST request: comment_payloads_from_gh\n" +\
                         "Probably, the request doesn't have the 'HTTP_X_HUB_SIGNATURE' header"
            return error_server_response(error_text, 400)

        payload = request.data
        put_task_in_queue(payload, 4)    # добавление задачи в очередь на обработку
        return standard_server_response('Github')
"""

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

        # проверка, что с данного ip разрешено принимать POST запросы
        try:
            sender_ip = request.META['REMOTE_ADDR']
            if(not chk_if_ip_is_allowed(sender_ip)):

                error_text = "ERROR: received POST request: payloads_from_rm\n" +\
                             "But the sender_ip doesn't match any of the allowed_ips\n" +\
                             "sender_ip: " + sender_ip + "\n"
                return error_server_response(error_text, 401)

        except:

            error_text = "ERROR: received POST request: payloads_from_rm\n" +\
                         "Probably, the request doesn't have the 'REMOTE_ADDR' header"
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
                         "Probably, the request doesn't have the 'REMOTE_ADDR' header"
            return error_server_response(error_text, 400)

        payload = json.dumps(request.data)  # превращаем QueryDict в JSON - сериализуемую строку
        payload = json.loads(payload)       # превращаем payload в JSON

        put_task_in_queue(payload, 1)       # добавление задачи в очередь на обработку

        server_response = 'you. Check the server logs for more detailed information.'
        return standard_server_response(server_response)

    """def create(self, request, *args, **kwargs):

        script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
        file_path_absolute = os.path.join(script_dir, "linked_projects_form.html")

        linked_projects_form = Linked_Projects_Form(field_order=["url_rm", "url_gh"])
        return render(request, file_path_absolute, {"form": linked_projects_form})"""

    queryset = Linked_Projects.objects.all()
    serializer_class = Linked_Projects_Serializer
