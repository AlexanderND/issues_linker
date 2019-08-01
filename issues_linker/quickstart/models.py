from django.db import models

from issues_linker.my_functions import tracker_ids_rm           # ids трекеров задачи в редмайне
from issues_linker.my_functions import status_ids_rm            # ids статусов задачи в редмайне
from issues_linker.my_functions import priority_ids_rm          # ids приоритетов задачи в редмайне

import queue

# ======================================================= GITHUB =======================================================


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


# убрал выше .save(), так как нет задачи сохранять на сервере резервную копию данных
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
    issue_num_gh = models.BigIntegerField(blank=1, null=1)          # issue['number'] в гитхабе (номер issue в репозитории)

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


"""# ================================================ ОЧЕРЕДЬ ОБРАБОТКИ ЗАДАЧ =============================================


''' Класс SingletonModel -  '''
class SingletonModel(models.Model):

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


''' Класс "Queue_Tasks" - задачи в очереди обработки задач '''
class Queue_Tasks_Manager(models.Manager):

    use_in_migrations = True


    def create_queue_task(self, task):

        queue_task = self.model(task=task)

        queue_task.save()   # сохранение queue_task в базе данных

        return queue_task


    def get_by_natural_key(self, id):
        return self.get(id=id)

class Queue_Tasks(models.Model):

    task = models.CharField(blank=1, max_length=256)    # краткое описание задачи

    db_table = 'queue_task'
    objects = Queue_Tasks_Manager()

    class Meta:
        verbose_name = 'queue_task'
        verbose_name_plural = 'queue_tasks'


''' Класс "Queue" - очередь обработки задач '''
class Queue_Manager(models.Manager):

    use_in_migrations = True


    def create_queue(self, project_id_rm, repos_id_gh, url_rm, url_gh):
        linked_projects = self.model(project_id_rm=project_id_rm,
                                     repos_id_gh=repos_id_gh,
                                     url_rm=url_rm,
                                     url_gh=url_gh)
        linked_projects.save()  # сохранение linked_projects в базе данных

        return linked_projects


    def get_by_natural_key(self, id):
        return self.get(id=id)

class Queue(SingletonModel):

    tasks = models.ManyToOneRel()


    # добавление в очередь
    def get_in_line(self, task):


        return 0

    # выход из очереди
    def get_out_of_line(self, task):

        return 0


    db_table = 'queue'
    objects = Queue_Manager()

    class Meta:
        verbose_name = 'queue'
        verbose_name_plural = 'queue'"""
