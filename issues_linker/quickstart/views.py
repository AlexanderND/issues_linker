#from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from issues_linker.quickstart.serializers import Payload_GH_Serializer, Payload_RM_Serializer, Linked_Issues_Serializer

from issues_linker.process_payload_from_gh import process_payload_from_gh    # загрузка issue в Redmine
from issues_linker.process_payload_from_rm import process_payload_from_rm    # загрузка issue в Github
from issues_linker.process_comment_payload_from_gh import process_comment_payload_from_gh     # загрузка комментариев к issue в Github
from issues_linker.quickstart.models import Payload_GH, Payload_RM, Linked_Issues  # мои модели

import json
from issues_linker.my_functions import WRITE_LOG

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
        # TODO: добавлять в очередь

        process_result = process_payload_from_gh(request.data)

        #return super(Payload_From_GH_ViewSet, self).create(request, *args, **kwargs)
        return process_result

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
        # TODO: добавлять в очередь

        process_result = process_comment_payload_from_gh(request.data)

        #return super(Comment_Payload_From_GH_ViewSet, self).create(request, *args, **kwargs)
        return process_result


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
        # TODO: добавлять в очередь

        process_result = process_payload_from_rm(request.data)

        #return super(Payload_From_RM_ViewSet, self).create(request, *args, **kwargs)
        return process_result


# ======================================================== СВЯЗЬ =======================================================


''' связынные issues '''
class Linked_Issues_ViewSet(viewsets.ModelViewSet):
    """
    Linked_Issues_ViewSet.
    Здесь хранится информация о том, какие issue связаны между собой.
    """
    queryset = Linked_Issues.objects.all()
    serializer_class = Linked_Issues_Serializer
