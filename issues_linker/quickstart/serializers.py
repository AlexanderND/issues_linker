#from django.contrib.auth.models import User, Group
from rest_framework import serializers

# мои модели (хранение на сервере)
from issues_linker.quickstart.models import Comment_Payload_GH, Payload_GH, Payload_RM

# мои модели (связь)
from issues_linker.quickstart.models import Linked_Projects, Linked_Issues, Linked_Comments

# мои модели (очередь обработки задач)
from issues_linker.quickstart.models_tasks_queue import Task_In_Queue, Tasks_Queue


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

    class Meta:
        model = Comment_Payload_GH
        fields = ('action', 'sender_id', 'sender_login', 'issue_author_id', 'issue_author_login', 'issue_title',
                  'issue_body', 'issue_id', 'project_id', 'issue_number', 'issue_url', 'comment_body',
                  'comment_id', 'comment_author_id', 'comment_author_login', 'comment_author_firstname',
                  'comment_author_lastname')

    def create(self, payload):
        parsed_payload = Comment_Payload_GH.objects.create_parsed_payload(payload)
        return parsed_payload

''' comment payloads от гитхаба '''
class Payload_GH_Serializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Payload_GH
        fields = ('action', 'sender_id', 'sender_login', 'issue_title', 'issue_body', 'issue_author_id',
                  'issue_author_login', 'issue_id', 'repos_id', 'issue_number', 'issue_url', 'issue_label')

    def create(self, payload):
        parsed_payload = Payload_GH.objects.create_parsed_payload(payload)
        return parsed_payload


# ======================================================= REDMINE ======================================================


''' payloads от редмайна '''
class Payload_RM_Serializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Payload_RM
        fields = ('action', 'issue_author_id', 'issue_author_login', 'issue_author_firstname', 'issue_author_lastname',
                  'comment_body', 'comment_id', 'comment_author_id', 'comment_author_login', 'comment_author_firstname',
                  'comment_author_lastname', 'issue_title', 'issue_body', 'tracker_id', 'status_id', 'priority_id',
                  'issue_id', 'project_id', 'issue_url')

    def create(self, payload):
        parsed_payload = Payload_RM.objects.create_parsed_payload(payload)
        return parsed_payload


# ======================================================== СВЯЗЬ =======================================================


''' связынные комментарии в issue'''
class Linked_Comments_Serializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Linked_Comments
        fields = ('comment_id_rm', 'comment_id_gh')

''' связынные issues в проекте '''
class Linked_Issues_Serializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Linked_Issues
        fields = ('issue_id_rm', 'issue_id_gh', 'repos_id_gh', 'issue_num_gh', 'comments',
                  'tracker_id_rm', 'status_id_rm', 'priority_id_rm', 'is_opened')

''' связынные проекты '''
class Linked_Projects_Serializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Linked_Projects
        fields = ('url_rm', 'url_gh', 'issues')
        read_only_fields = ('project_id_rm', 'repos_id_gh')


# ================================================ ОЧЕРЕДЬ ОБРАБОТКИ ЗАДАЧ =============================================


''' задачи в очереди обработки задач '''
class Task_In_Queue_Serializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Task_In_Queue
        fields = ('type', 'payload')

''' очередь обработки задач '''
class Tasks_Queue_Serializer(serializers.HyperlinkedModelSerializer):
    #tasks_queue = Tasks_In_Queue_Serializer(many=True, read_only=True)

    class Meta:
        model = Tasks_Queue
        fields = (['tasks_in_queue'])
