from collections import deque                           # двухсторонняя очередь в питоне

from django.db import models

from issues_linker.my_functions import WRITE_LOG        # ведение логов

from django.core.exceptions import ObjectDoesNotExist   # обработка исключений: объект не найден

# задержка
import time


# ======================================================= GITHUB =======================================================
# убрал .save(), так как нет задачи сохранять на сервере резервную копию данных


'''Класс "Issue_GH" - поле "Issue" (title, body, url, number, id) в классе "Payload_GH" - Issue в гитхабе'''
class Issue_GH_Manager(models.Manager):
    use_in_migrations = True

    def create_issue(self, issue):
        # Creates and saves an Issue with the given title, body and url.
        issue_ = self.model(title=issue['title'],
                           body=issue['body'],
                           url=issue['url'],
                           number=issue['number'],
                           id_gh=issue['id_gh'])

        #issue_.save()   # сохранение issue в бвзе данных
        return issue_

    def get_by_natural_key(self, id):
        return self.get(id=id)

class Issue_GH(models.Model):
    title = models.CharField(blank=1,
                             max_length=256)    # 256 - максимальная длина title  в гитхабе
    body = models.CharField(blank=1,
                            max_length=65536)   # 65536 - максимальная (?) длина body  в гитхабе
    url = models.CharField(max_length=512)      # 512 - в 2 раза больше максимальной длины title
    id_gh = models.IntegerField()               # id issue в гитхабе
    number = models.IntegerField()              # номер issue в репозитории

    db_table = 'issue_fields_gh'
    objects = Issue_GH_Manager()

    class Meta:
        verbose_name = 'issue_field_gh'
        verbose_name_plural = 'issue_fields_gh'


'''Класс "Repository_GH" - для хранения id репозитория в гитхабе'''
class Repository_GH_Manager(models.Manager):
    use_in_migrations = True

    def create_gh_repository(self, repository):
        repository_ = self.model(id_gh=repository['id_gh'])
        #repository_.save()

        return repository_

    def get_by_natural_key(self, id):
        return self.get(id=id)

class Repository_GH(models.Model):
    id_gh = models.IntegerField()               # repository id  в гитхабе

    db_table = 'repositories_gh'

    objects = Repository_GH_Manager()

    class Meta:
        verbose_name = 'repository_gh'
        verbose_name_plural = 'repositories_gh'


'''Класс "Payload_GH" (action, issue(title, body, url)) - payload-ы с гитхаба'''
class Payload_GH_Manager(models.Manager):
    use_in_migrations = True

    def create_payload(self, validated_data):
        issue = Issue_GH.objects.create_issue(
            validated_data.pop('issue'))

        repository = Repository_GH.objects.create_gh_repository(
            validated_data.pop('repository'))

        payload = self.model(action=validated_data.pop('action'),
                             issue=issue,
                             repository=repository)
        #payload.save()

        return payload

    def get_by_natural_key(self, id):
        return self.get(id=id)

class Payload_GH(models.Model):
    action = models.CharField(blank=1,
                              max_length=20)    # совершённое действие (opened, closed, reopened и т.п.)
    issue = models.OneToOneField(
        Issue_GH,
        on_delete=models.CASCADE,
        default=None)                           # сожержимое issue (title, body и т.п.)
    repository = models.OneToOneField(
        Repository_GH,
        on_delete=models.CASCADE,
        default=None)                           # содержимое repository (id)

    db_table = 'payloads_from_gh'

    objects = Payload_GH_Manager()

    class Meta:
        verbose_name = 'payload_from_gh'
        verbose_name_plural = 'payloads_from_gh'


# ======================================================= REDMINE ======================================================
# убрал .save(), так как нет задачи сохранять на сервере резервную копию данных


'''Класс "Project_RM" - для хранения id репозитория в редмайне'''
class Project_RM_Manager(models.Manager):
    use_in_migrations = True

    def create_rm_project(self, project):
        # Creates and saves an Issue with the given title, body and url.
        project_ = self.model(id_rm=project['id_rm'])

        #project_.save()   # сохранение issue в бвзе данных
        return project_

    def get_by_natural_key(self, id):
        return self.get(id=id)

class Project_RM(models.Model):
    id_rm = models.IntegerField()               # id проекта в редмайне

    db_table = 'projects_rm'
    objects = Project_RM_Manager()

    class Meta:
        verbose_name = 'project_rm'
        verbose_name_plural = 'projects_rm'


'''Класс "Issue_RM" - поле "Issue" (title, body, url, id) в классе "Payload_RM" - Issue в редмайне'''
class Issue_RM_Manager(models.Manager):
    use_in_migrations = True

    def create_issue(self, issue):
        # Creates and saves an Issue with the given title, body and url.
        project = Project_RM.objects.create_rm_project(
            issue['project'])

        issue_ = self.model(title=issue['title'],
                            body=issue['body'],
                            id_rm=issue['id_rm'],
                            project=project)

        #issue_.save()   # сохранение issue в бвзе данных
        return issue_

    def get_by_natural_key(self, id):
        return self.get(id=id)

class Issue_RM(models.Model):
    title = models.CharField(blank=1,
                             max_length=256)    # 256 - максимальная (?) длина title  в редмайне (гитхабе)
    body = models.CharField(blank=1,
                            max_length=65536)   # 65536 - максимальная (?) длина body  в редмайне (гитхабе)
    id_rm = models.IntegerField()               # id issue в редмайне
    project = models.OneToOneField(
        Project_RM,
        on_delete=models.CASCADE,
        default=None)                           # содержимое project (id)

    db_table = 'issue_fields_rm'
    objects = Issue_RM_Manager()

    class Meta:
        verbose_name = 'issue_field_rm'
        verbose_name_plural = 'issue_fields_rm'


'''Класс "Payload_RM_Field" (action, issue(title, body, id)) - хранит payload-ы с редмайна'''
class Payload_RM_Field_Manager(models.Manager):
    use_in_migrations = True

    def create_payload(self, validated_data):
        issue = Issue_RM.objects.create_issue(
            validated_data.pop('issue'))

        payload = self.model(action=validated_data.pop('action'),
                             issue=issue)
        #payload.save()

        return payload

    def get_by_natural_key(self, id):
        return self.get(id=id)

class Payload_RM_Field(models.Model):
    action = models.CharField(blank=1,
                              max_length=20)
    issue = models.OneToOneField(
        Issue_RM,
        on_delete=models.CASCADE,
        default=None)

    db_table = 'payload_fields_from_rm'

    objects = Payload_RM_Field_Manager()

    class Meta:
        verbose_name = 'payload_field_from_rm'
        verbose_name_plural = 'payload_fields_from_rm'


'''Класс "Payload_RM" хранит поле Payload_RM_Field - payload-ы с редмайна'''
class Payload_RM_Manager(models.Manager):
    use_in_migrations = True

    def create_payload(self, validated_data):
        payload_field = Payload_RM_Field.objects.create_payload(
            validated_data.pop('payload_field'))

        payload = self.model(payload_field=payload_field)
        #payload.save()

        return payload

    def get_by_natural_key(self, id):
        return self.get(id=id)

class Payload_RM(models.Model):
    payload_field = models.OneToOneField(
        Payload_RM_Field,
        on_delete=models.CASCADE,
        default=None)

    db_table = 'payloads_from_rm'

    objects = Payload_RM_Manager()

    class Meta:
        verbose_name = 'payload_from_rm'
        verbose_name_plural = 'payloads_from_rm'


# ==================================================== СВЯЗЬ COMMENTS ==================================================


'''Класс "Linked_Comments" - связанные комментарии в issue (comment_id_rm - comment_id_gh, linked_issues_id)'''
class Linked_Comments_Manager(models.Manager):
    use_in_migrations = True

    def create_linked_comments(self, comment_id_rm, comment_id_gh):
        linked_comments = self.model(comment_id_rm=comment_id_rm,
                                     comment_id_gh=comment_id_gh)
        linked_comments.save()  # сохранение linked_comments в базе данных

        return linked_comments

    def add_comment_id_rm(self, comment_id_rm):
        self.edit(comment_id_rm=comment_id_rm)


    def get_by_natural_key(self, id):
        return self.get(id=id)

    def get_by_comment_id_rm(self, comment_id_rm):
        return self.filter(comment_id_rm=comment_id_rm)

    def get_by_comment_id_gh(self, comment_id_gh):
        return self.filter(comment_id_gh=comment_id_gh)

class Linked_Comments(models.Model):

    comment_id_rm = models.BigIntegerField(blank=1, null=1)     # id комментария в редмайне
    comment_id_gh = models.BigIntegerField(blank=1, null=1)     # id комментария в гитхабе

    db_table = 'linked_comments'
    objects = Linked_Comments_Manager()

    class Meta:
        verbose_name = 'linked_comments'
        verbose_name_plural = 'linked_comments'


# ===================================================== СВЯЗЬ ISSUES ===================================================


# TODO: при удалении linked_issues linked_comments не удаляются (использовать что-то другое, вместо ManyToMany (https://stackoverflow.com/questions/3937194/django-cascade-deletion-in-manytomanyrelation))
'''Класс "Linked_Issues" - связанные issues (issue_id_rm - repo_id_gh, issue_id_gh)'''
class Linked_Issues_Manager(models.Manager):
    use_in_migrations = True

    def create_linked_issues(self, issue_id_rm, issue_id_gh, repos_id_gh, issue_num_gh,
                             tracker_id_rm, status_id_rm, priority_id_rm):
        linked_issues = self.model(issue_id_rm=issue_id_rm,
                                   issue_id_gh=issue_id_gh,
                                   repos_id_gh=repos_id_gh,
                                   issue_num_gh=issue_num_gh,
                                   tracker_id_rm=tracker_id_rm,
                                   status_id_rm=status_id_rm,
                                   priority_id_rm=priority_id_rm)
        linked_issues.save()  # сохранение linked_issues в базе данных

        return linked_issues

    def get_by_natural_key(self, id):
        return self.get(id=id)

    def get_by_issue_id_rm(self, issue_id_rm):
        return self.filter(issue_id_rm=issue_id_rm)

    def get_by_issue_id_gh(self, issue_id_gh):
        return self.filter(issue_id_gh=issue_id_gh)

class Linked_Issues(models.Model):
    issue_id_rm = models.BigIntegerField(blank=1, null=1)           # id issue в редмайне
    issue_id_gh = models.BigIntegerField(blank=1, null=1)           # id issue в гитхабе

    repos_id_gh = models.BigIntegerField(blank=1, null=1)           # id репозитория в гитхабе
    issue_num_gh = models.BigIntegerField(blank=1, null=1)          # номер issue в репозитории гитхаба

    # различные id-шники в редмайне (или label-ы в гитхабе)
    tracker_id_rm = models.IntegerField(blank=1, null=1)
    status_id_rm = models.IntegerField(blank=1, null=1)
    priority_id_rm = models.IntegerField(blank=1, null=1)

    # состояние issue: закрыт / открыт
    is_opened = models.BooleanField(default=True)

    comments = models.ManyToManyField(Linked_Comments, blank=1)     # комментарии к issue


    def add_comment(self, comment_id_rm, comment_id_gh):
        comment = Linked_Comments.objects.create_linked_comments(
            comment_id_rm,
            comment_id_gh)

        self.comments.add(comment)

        return comment

    def get_comment_by_id_gh(self, comment_id_gh):
        return Linked_Comments.objects.get_by_comment_id_gh(comment_id_gh)

    def get_comment_by_id_rm(self, comment_id_rm):
        return Linked_Comments.objects.get_by_comment_id_rm(comment_id_rm)

    db_table = 'linked_issues'
    objects = Linked_Issues_Manager()

    class Meta:
        verbose_name = 'linked_issues'
        verbose_name_plural = 'linked_issues'

# ==================================================== СВЯЗЬ PROJECTS ==================================================


'''Класс "Linked_Projects" - связанные projects (project_id_rm - repo_id_gh)'''
class Linked_Projects_Manager(models.Manager):

    use_in_migrations = True


    def create_linked_projects(self, project_id_rm, repos_id_gh, url_rm, url_gh):
        linked_projects = self.model(project_id_rm=project_id_rm,
                                     repos_id_gh=repos_id_gh,
                                     url_rm=url_rm,
                                     url_gh=url_gh)
        linked_projects.save()  # сохранение linked_projects в базе данных

        return linked_projects


    def get_by_natural_key(self, id):
        return self.get(id=id)

    def get_by_project_id_rm(self, project_id_rm):
        return self.filter(project_id_rm=project_id_rm)

    def get_by_repos_id_gh(self, repos_id_gh):
        return self.filter(repos_id_gh=repos_id_gh)

class Linked_Projects(models.Model):

    # используются для привязки проектов
    project_id_rm = models.BigIntegerField(blank=1, null=1)         # id проекта в редмайне
    repos_id_gh = models.BigIntegerField(blank=1, null=1)           # id репозитория в гитхабе

    # ссылки - используются лишь для получения id проектов, но более удобны лдя человека
    url_rm = models.CharField(blank=1, max_length=256)              # ссылка на проект в редмайне
    url_gh = models.CharField(blank=1, max_length=256)              # ссылка на проект в гитхабе

    issues = models.ManyToManyField(Linked_Issues, blank=1)         # задачи в проекте


    def add_linked_issues(self, linked_issues):

        self.issues.add(linked_issues)

        return linked_issues


    def get_issue_by_id_gh(self, issue_id_gh):
        return Linked_Issues.objects.get_by_issue_id_gh(issue_id_gh)

    def get_issue_by_id_rm(self, issue_id_rm):
        return Linked_Issues.objects.get_by_issue_id_rm(issue_id_rm)


    db_table = 'linked_projects'
    objects = Linked_Projects_Manager()

    class Meta:
        verbose_name = 'linked_projects'
        verbose_name_plural = 'linked_projects'


# ================================================ ОЧЕРЕДЬ ОБРАБОТКИ ЗАДАЧ =============================================


''' Класс "Tasks_In_Queue" - задачи в очереди обработки задач '''
'''class Tasks_In_Queue_Manager(models.Manager):

    use_in_migrations = True


    def create_task_in_queue(self, project_id_rm, repos_id_gh,
                             issue_id_rm, issue_id_gh,
                             comment_id_rm, comment_id_gh):

        task_in_queue = self.model(project_id_rm, repos_id_gh,
                                   issue_id_rm, issue_id_gh,
                                   comment_id_rm, comment_id_gh)

        task_in_queue.save()   # сохранение queue_task в базе данных

        return task_in_queue


    def get_by_natural_key(self, id):

        try:
            task_in_queue = self.get(id=id)

        except ObjectDoesNotExist:
            task_in_queue = None

        return task_in_queue

    def get_natural_key(self):
        return self.id


    # ПРОЕКТЫ
    def get_by_project_id_rm(self, project_id_rm):
        return self.get(project_id_rm=project_id_rm)

    def get_by_repos_id_gh(self, repos_id_gh):
        return self.get(repos_id_gh=repos_id_gh)

    # ЗАДАЧИ
    def get_by_issue_id_rm(self, issue_id_rm):
        return self.get(issue_id_rm=issue_id_rm)

    def get_by_issue_id_gh(self, issue_id_gh):
        return self.get(issue_id_gh=issue_id_gh)

    # КОММЕНТАРИИ
    def get_by_comment_id_rm(self, comment_id_rm):
        return self.get(comment_id_rm=comment_id_rm)

    def get_by_comment_id_gh(self, comment_id_gh):
        return self.get(comment_id_gh=comment_id_gh)

class Tasks_In_Queue(models.Model):

    # ПРОЕКТЫ
    project_id_rm = models.BigIntegerField(blank=1, null=1)     # id проекта в редмайне
    repos_id_gh = models.BigIntegerField(blank=1, null=1)       # id репозитория в гитхабе

    # ЗАДАЧИ
    issue_id_rm = models.BigIntegerField(blank=1, null=1)       # id issue в редмайне
    issue_id_gh = models.BigIntegerField(blank=1, null=1)       # id issue в гитхабе

    # КОММЕНТАРИИ
    comment_id_rm = models.BigIntegerField(blank=1, null=1)     # id комментария в редмайне
    comment_id_gh = models.BigIntegerField(blank=1, null=1)     # id комментария в гитхабе

    def create_task_in_queue(self, project_id_rm, repos_id_gh,
                             issue_id_rm, issue_id_gh,
                             comment_id_rm, comment_id_gh):

        task_in_queue = self.objects.create_task_in_queue(project_id_rm, repos_id_gh,
                                                          issue_id_rm, issue_id_gh,
                                                          comment_id_rm, comment_id_gh)

        return task_in_queue


    db_table = 'queue_task'
    objects = Tasks_In_Queue_Manager()

    class Meta:
        verbose_name = 'queue_task'
        verbose_name_plural = 'queue_tasks'''
class Tasks_In_Queue():

    '''# ПРОЕКТЫ
    project_id_rm = int()
    repos_id_gh = int()

    # ЗАДАЧИ
    issue_id_rm = int()
    issue_id_gh = int()

    # КОММЕНТАРИИ
    comment_id_rm = int()
    comment_id_gh = int()

    def create(self, project_id_rm, repos_id_gh,
               issue_id_rm, issue_id_gh,
               comment_id_rm, comment_id_gh):

        # ПРОЕКТЫ
        self.project_id_rm = project_id_rm
        self.repos_id_gh = repos_id_gh

        # ЗАДАЧИ
        self.issue_id_rm = issue_id_rm
        self.issue_id_gh = issue_id_gh

        # КОММЕНТАРИИ
        self.comment_id_rm = comment_id_rm
        self.comment_id_gh = comment_id_gh

        return self'''


    ''' 1 - link_projects '''
    ''' 2 - process_payload_from_rm '''
    ''' 3 - process_payload_from_gh '''
    ''' 4 - process_comment_payload_from_gh '''
    type = int()    # тип задачи (какой файл запускать)

    id = int()      # id задачи

    def create(self, type, id):

        # ПРОЕКТЫ
        self.type = type
        self.id = id

        return self

''' Класс "Queue" - очередь обработки задач '''
class Queue_Manager(models.Manager):

    use_in_migrations = True


    def creqte_queue(self):

        queue = self.model()
        queue.save()   # сохранение queue_test в базе данных

        return queue

    def get_by_natural_key(self, id):

        try:
            queue = self.get(id=id)

        except ObjectDoesNotExist:
            queue = None

        return queue

    def get_all(self):

        queue = self.all()

        if (len(queue) < 1):
            queue = None

        else:
            queue = queue[0]

        return queue

# ожидание очереди
def wait(queue, task_in_queue):
    #return 0

    # цикл проверки, не подошла ли очередь
    while True:

        # пропускаем ошибку 'database is locked'
        '''try:
            # прекращаем ожидание, если данный объект является самым левым в очереди
            if (queue[0] == task_in_queue):

                return 0
        except:
            pass'''

        time.sleep(1)     # небольшая задержка, перед повторной попыткой (чтобы не перегружать сервер)

        try:
            # прекращаем ожидание, если данный объект является самым левым в очереди
            if (queue[0] == task_in_queue):

                return 0
        except:
            # прекращаем ожидание, если очередь пуста
            return 0

# TODO: исправить id проверки первой записи (начинаются с 1?)
class Queue(models.Model):

    queue = deque()                                             # очередь задач


    # занесение project в очередь
    """def project_in_line(self, project_id_rm, repos_id_gh):

        task_in_queue = Tasks_In_Queue()
        task_in_queue = task_in_queue.create(project_id_rm, repos_id_gh,
                                             None, None,
                                             None, None)

        '''task_in_queue = Tasks_In_Queue(project_id_rm, repos_id_gh,
                                       None, None,
                                       None, None)
        task_in_queue.save()'''

        self.queue.append(task_in_queue)    # занесение задачи в очередь

        return wait(self.queue, task_in_queue)

    # занесение issue в очередь
    def issue_in_line(self, issue_id_rm, issue_id_gh):

        task_in_queue = Tasks_In_Queue()
        task_in_queue = task_in_queue.create(None, None,
                                             issue_id_rm, issue_id_gh,
                                             None, None)

        '''task_in_queue = Tasks_In_Queue(None, None,
                                       issue_id_rm, issue_id_gh,
                                       None, None)
        task_in_queue.save()'''

        self.queue.append(task_in_queue)    # занесение задачи в очередь

        return wait(self.queue, task_in_queue)

    # занесение comment в очередь
    def comment_in_line(self, comment_id_rm, comment_id_gh):

        task_in_queue = Tasks_In_Queue()
        task_in_queue = task_in_queue.create(None, None,
                                             None, None,
                                             comment_id_rm, comment_id_gh)

        '''task_in_queue = Tasks_In_Queue(None, None,
                                       None, None,
                                       comment_id_rm, comment_id_gh)
        task_in_queue.save()'''

        self.queue.append(task_in_queue)    # занесение задачи в очередь"""
    def get_in_line(self, type):

        # создаём id элемента
        if (len(self.queue) < 1):
            last_task_in_queue_id = 0

        else:
            last_task_in_queue_id = self.queue[-1].id           # peek на последний элемент в очереди

        task_in_queue = Tasks_In_Queue()
        task_in_queue = task_in_queue.create(type, last_task_in_queue_id + 1)

        '''task_in_queue = Tasks_In_Queue(project_id_rm, repos_id_gh,
                                       None, None,
                                       None, None)
        task_in_queue.save()'''

        self.queue.append(task_in_queue)    # занесение задачи в очередь

        return wait(self.queue, task_in_queue)

    # удаление задачи из очереди
    def task_out_of_line(self):

        task_in_queue = self.queue.popleft()    # удаление задачи из очереди
        #task_in_queue.delete()                  # удаление задачи из базы данных

        return 0


    # ЗАГРУЗКА ОЧЕРЕДИ (если не создана - создаём, если создана - отправляем)
    @classmethod
    def load(self):

        queue = self.objects.get_all()
        WRITE_LOG(queue)

        if (queue == None):
            queue = Queue.objects.creqte_queue()

        return queue


    db_table = 'queue_test'
    objects = Queue_Manager()

    class Meta:
        verbose_name = 'queue_test'
        verbose_name_plural = 'queue_test'
