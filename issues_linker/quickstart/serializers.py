#from django.contrib.auth.models import User, Group
from rest_framework import serializers

# мои модели (хранение на сервере)
from issues_linker.quickstart.models import Issue_GH, Repository_GH, Payload_GH,\
    Project_RM, Issue_RM, Payload_RM_Field, Payload_RM

# мои модели (связь)
from issues_linker.quickstart.models import Linked_Projects, Linked_Issues, Linked_Comments

# мои модели (очередь обработки задач)
#from issues_linker.quickstart.models import Tasks_In_Queue, Queue
from issues_linker.quickstart.models import Tasks_Queue


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


''' issues в гитхабе '''
class Issue_GH_Serializer(serializers.HyperlinkedModelSerializer):
    # изменяем название поля id (так как прилетает 'id' а не 'id_gh')
    id = serializers.IntegerField(source='id_gh')

    class Meta:
        model = Issue_GH
        fields = ('title', 'body', 'url', 'number', 'id')

''' repository в гитхабе '''
class Repository_GH_Serializer(serializers.HyperlinkedModelSerializer):
    # изменяем название поля id (так как прилетает 'id' а не 'id_gh')
    id = serializers.IntegerField(source='id_gh')

    class Meta:
        model = Repository_GH
        fields = (['id'])

''' payloads от гитхаба '''
class Payload_GH_Serializer(serializers.HyperlinkedModelSerializer):
    issue = Issue_GH_Serializer(many=False, read_only=False)
    repository = Repository_GH_Serializer(many=False, read_only=False)

    class Meta:
        model = Payload_GH
        fields = ('action', 'issue', 'repository')

    # для работы с OneToOne полем
    def create(self, validated_data):
        payload = Payload_GH.objects.create_payload(validated_data)
        return payload


# ======================================================= REDMINE ======================================================


''' projects в редмайне '''
class Project_RM_Serializer(serializers.HyperlinkedModelSerializer):
    # изменяем название полей, т.к. названия в модели стандартизированы под гитхаб (короче и удобней)
    id = serializers.IntegerField(source='id_rm')

    class Meta:
        model = Project_RM
        fields = (['id'])

''' issues в редмайне '''
class Issue_RM_Serializer(serializers.HyperlinkedModelSerializer):
    # изменяем название полей, т.к. названия в модели стандартизированы под гитхаб (короче и удобней)
    subject = serializers.CharField(source='title')
    description = serializers.CharField(allow_blank=1, source='body')
    id = serializers.IntegerField(source='id_rm')
    project = Project_RM_Serializer(many=False, read_only=False)

    class Meta:
        model = Issue_RM
        fields = ('subject', 'description', 'id', 'project')

''' поле payloads от редмайна '''
class Payload_RM_Field_Serializer(serializers.HyperlinkedModelSerializer):
    issue = Issue_RM_Serializer(many=False, read_only=False)

    class Meta:
        model = Payload_RM_Field
        fields = ('action', 'issue')

    # для работы с OneToOne полем
    def create(self, validated_data):
        payload = Payload_RM_Field.objects.create_payload(validated_data)
        return payload

''' payloads от редмайна '''
class Payload_RM_Serializer(serializers.HyperlinkedModelSerializer):
    payload = Payload_RM_Field_Serializer(many=False, read_only=False, source='payload_field')

    class Meta:
        model = Payload_RM
        fields = (['payload'])

    # для работы с OneToOne полем
    def create(self, validated_data):
        payload = Payload_RM.objects.create_payload(validated_data)
        return payload


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
'''class Tasks_In_Queue_Serializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Tasks_In_Queue
        fields = ('project_id_rm', 'repos_id_gh',
                  'issue_id_rm', 'issue_id_gh',
                  'comment_id_rm', 'comment_id_gh')'''

''' очередь обработки задач '''
class Tasks_Queue_Serializer(serializers.HyperlinkedModelSerializer):
    #tasks = Tasks_In_Queue_Serializer(many=True, read_only=True)

    class Meta:
        model = Tasks_Queue
        fields = (['queue'])
