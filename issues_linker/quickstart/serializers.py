#from django.contrib.auth.models import User, Group
from rest_framework import serializers

# мои модели (хранение на сервере)
from issues_linker.quickstart.models import Comment_Payload_GH, Payload_GH, Payload_RM

# мои модели (связь)
from issues_linker.quickstart.models import Linked_Projects, Linked_Issues, Linked_Comments
from issues_linker.quickstart.models import Linked_Projects_Manager, Linked_Issues_Manager, Linked_Comments_Manager

# мои модели (очередь обработки задач)
from issues_linker.quickstart.models_tasks_queue import Task_In_Queue, Tasks_Queue

# последовательность действий при запуске сервера
from issues_linker.quickstart.server_startup import server_startup



'''# testing
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')'''


# ======================================================= GITHUB =======================================================


''' payloads от гитхаба '''
class Comment_Payload_GH_Serializer(serializers.HyperlinkedModelSerializer):

    id = serializers.IntegerField(read_only=True)

    action = serializers.CharField(read_only=True)
    sender_id = serializers.IntegerField(read_only=True)
    sender_login = serializers.CharField(read_only=True)
    issue_author_id = serializers.IntegerField(read_only=True)
    issue_author_login = serializers.CharField(read_only=True)
    issue_title = serializers.CharField(read_only=True)
    issue_body = serializers.CharField(read_only=True)
    issue_id = serializers.IntegerField(read_only=True)
    project_id = serializers.IntegerField(read_only=True)
    issue_number = serializers.IntegerField(read_only=True)
    issue_url = serializers.CharField(read_only=True)
    comment_body = serializers.CharField(read_only=True)
    comment_id = serializers.IntegerField(read_only=True)
    comment_author_id = serializers.IntegerField(read_only=True)
    comment_author_login = serializers.CharField(read_only=True)


    class Meta:
        model = Comment_Payload_GH
        fields = ('id', 'action', 'sender_id', 'sender_login', 'issue_author_id', 'issue_author_login', 'issue_title',
                  'issue_body', 'issue_id', 'project_id', 'issue_number', 'issue_url', 'comment_body',
                  'comment_id', 'comment_author_id', 'comment_author_login')

    def create(self, payload):
        parsed_payload = Comment_Payload_GH.objects.create_parsed_payload(payload)
        return parsed_payload

''' comment payloads от гитхаба '''
class Payload_GH_Serializer(serializers.HyperlinkedModelSerializer):

    id = serializers.IntegerField(read_only=True)

    action = serializers.CharField(read_only=True)
    sender_id = serializers.IntegerField(read_only=True)
    sender_login = serializers.CharField(read_only=True)
    issue_title = serializers.CharField(read_only=True)
    issue_body = serializers.CharField(read_only=True)
    issue_author_id = serializers.IntegerField(read_only=True)
    issue_author_login = serializers.CharField(read_only=True)
    issue_id = serializers.IntegerField(read_only=True)
    repos_id = serializers.IntegerField(read_only=True)
    issue_number = serializers.IntegerField(read_only=True)
    issue_url = serializers.CharField(read_only=True)
    issue_label = serializers.IntegerField(read_only=True)


    class Meta:
        model = Payload_GH
        fields = ('id', 'action', 'sender_id', 'sender_login', 'issue_title', 'issue_body', 'issue_author_id',
                  'issue_author_login', 'issue_id', 'repos_id', 'issue_number', 'issue_url', 'issue_label')

    def create(self, payload):
        parsed_payload = Payload_GH.objects.create_parsed_payload(payload)
        return parsed_payload


# ======================================================= REDMINE ======================================================


''' payloads от редмайна '''
class Payload_RM_Serializer(serializers.HyperlinkedModelSerializer):

    id = serializers.IntegerField(read_only=True)

    action = serializers.CharField(read_only=True)
    issue_author_id = serializers.IntegerField(read_only=True)
    issue_author_login = serializers.CharField(read_only=True)
    issue_author_firstname = serializers.CharField(read_only=True)
    issue_author_lastname = serializers.CharField(read_only=True)
    comment_body = serializers.CharField(read_only=True)
    comment_id = serializers.IntegerField(read_only=True)
    comment_author_id = serializers.IntegerField(read_only=True)
    comment_author_login = serializers.CharField(read_only=True)
    comment_author_firstname = serializers.CharField(read_only=True)
    comment_author_lastname = serializers.CharField(read_only=True)
    issue_title = serializers.CharField(read_only=True)
    issue_body = serializers.CharField(read_only=True)
    tracker_id = serializers.IntegerField(read_only=True)
    status_id = serializers.IntegerField(read_only=True)
    priority_id = serializers.IntegerField(read_only=True)
    issue_id = serializers.IntegerField(read_only=True)
    project_id = serializers.IntegerField(read_only=True)
    issue_url = serializers.CharField(read_only=True)


    class Meta:
        model = Payload_RM
        fields = ('id', 'action', 'issue_author_id', 'issue_author_login', 'issue_author_firstname', 'issue_author_lastname',
                  'comment_body', 'comment_id', 'comment_author_id', 'comment_author_login', 'comment_author_firstname',
                  'comment_author_lastname', 'issue_title', 'issue_body', 'tracker_id', 'status_id', 'priority_id',
                  'issue_id', 'project_id', 'issue_url')

    def create(self, payload):
        parsed_payload = Payload_RM.objects.create_parsed_payload(payload)
        return parsed_payload


# ======================================================== СВЯЗЬ =======================================================


''' связынные комментарии в issue'''
class Linked_Comments_Serializer(serializers.HyperlinkedModelSerializer):

    id = serializers.IntegerField(read_only=True)

    comment_id_rm = serializers.IntegerField(read_only=True)
    comment_id_gh = serializers.IntegerField(read_only=True)


    class Meta:
        model = Linked_Comments
        fields = ('id', 'comment_id_rm', 'comment_id_gh')

''' связынные issues в проекте '''
class Linked_Issues_Serializer(serializers.HyperlinkedModelSerializer):

    id = serializers.IntegerField(read_only=True)

    issue_id_rm = serializers.IntegerField(read_only=True)
    issue_id_gh = serializers.IntegerField(read_only=True)
    repos_id_gh = serializers.IntegerField(read_only=True)
    issue_num_gh = serializers.IntegerField(read_only=True)
    tracker_id_rm = serializers.IntegerField(read_only=True)
    status_id_rm = serializers.IntegerField(read_only=True)
    priority_id_rm = serializers.IntegerField(read_only=True)
    is_opened = serializers.BooleanField(read_only=True)

    comments = Linked_Comments_Serializer(many=True, read_only=True)


    class Meta:
        model = Linked_Issues
        fields = ('id', 'issue_id_rm', 'issue_id_gh', 'repos_id_gh', 'issue_num_gh',
                  'tracker_id_rm', 'status_id_rm', 'priority_id_rm', 'is_opened', 'comments')

''' связынные проекты '''
class Linked_Projects_Serializer(serializers.HyperlinkedModelSerializer):

    id = serializers.IntegerField(read_only=True)

    project_id_rm = serializers.IntegerField(read_only=True)
    repos_id_gh = serializers.IntegerField(read_only=True)
    last_link_time = serializers.DateTimeField(read_only=True)

    issues = Linked_Issues_Serializer(many=True, read_only=True)

    class Meta:
        model = Linked_Projects
        fields = ('id', 'url_rm', 'url_gh', 'last_link_time', 'project_id_rm', 'repos_id_gh', 'issues')


# ================================================ ОЧЕРЕДЬ ОБРАБОТКИ ЗАДАЧ =============================================


''' задача в очереди обработки задач '''
"""class Task_In_Queue_Serializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Task_In_Queue
        fields = ('type', 'payload')"""

''' очередь обработки задач '''
class Tasks_Queue_Serializer(serializers.HyperlinkedModelSerializer):

    id = serializers.IntegerField(read_only=True)
    #tasks_in_queue = Task_In_Queue_Serializer(many=True, read_only=True)

    class Meta:
        model = Tasks_Queue
        #fields = (['tasks_in_queue'])
        fields = ('id', 'queue')


# =================================================== ЗАГРУЗКА СЕРВЕРА =================================================


server_startup()
