from collections import deque                           # двухсторонняя очередь в питоне

from django.db import models
from django.utils import timezone

from issues_linker.my_functions import WRITE_LOG        # ведение логов

from django.core.exceptions import ObjectDoesNotExist   # обработка исключений: объект не найден

import datetime

# TODO: связь гитхаба с нисколькими серверами редмайна (?)


# ======================================================= GITHUB =======================================================


''' Класс "Comment_Payload_GH" - payload-ы комментариев с гитхаба '''
class Comment_Payload_GH_Manager(models.Manager):
    use_in_migrations = True

    def create_parsed_payload(self, payload):

        # совершённое действие и его автор
        self.action = payload['action']
        self.sender_id = payload['sender']['id']
        self.sender_login = payload['sender']['login']

        # автор issue
        self.issue_author_id = payload['issue']['user']['id']
        self.issue_author_login = payload['issue']['user']['login']

        # поля issue
        self.issue_title = payload['issue']['title']
        self.issue_body = payload['issue']['body']

        # идентификаторы (для связи и логов)
        self.issue_id = payload['issue']['id']
        self.project_id = payload['repository']['id']
        self.issue_number = payload['issue']['number']

        # ссылка на issue (для фразы бота и логов)
        self.issue_url = payload['issue']['html_url']

        # тело комментария
        self.comment_body = payload['comment']['body']

        # id комментария (для связи и логов)
        self.comment_id = payload['comment']['id']

        # автор комментария
        self.comment_author_id = payload['comment']['user']['id']
        self.comment_author_login = payload['comment']['user']['login']

        self.save()
        return self

    def get_by_natural_key(self, id):
        return self.get(id=id)

class Comment_Payload_GH(models.Model):

    # совершённое действие и его автор
    action = models.TextField(blank=1)
    sender_id = models.IntegerField(blank=1, null=1)
    sender_login = models.TextField(blank=1)

    # автор issue
    issue_author_id = models.IntegerField(blank=1, null=1)
    issue_author_login = models.TextField(blank=1)

    # поля issue
    issue_title = models.TextField(blank=1)
    issue_body = models.TextField(blank=1)

    # идентификаторы (для связи и логов)
    issue_id = models.IntegerField(blank=1, null=1)
    project_id = models.IntegerField(blank=1, null=1)
    issue_number = models.IntegerField(blank=1, null=1)

    # ссылка на issue (для фразы бота и логов)
    issue_url = models.TextField(blank=1, max_length=512)

    # тело комментария
    comment_body = models.TextField(blank=1)

    # id комментария (для связи и логов)
    comment_id = models.IntegerField(blank=1, null=1)

    # автор комментария
    comment_author_id = models.IntegerField(blank=1, null=1)
    comment_author_login = models.TextField(blank=1)


    db_table = 'payloads_from_rm'
    objects = Comment_Payload_GH_Manager()

    class Meta:
        verbose_name = 'payload_from_rm'
        verbose_name_plural = 'payloads_from_rm'

# TODO: ПЕРЕДЕЛАТЬ ЛОГИКУ КОРРЕКТИРОВАНИЯ LABELS!!!
''' Класс "Payload_GH" - payload-ы с гитхаба '''
class Payload_GH_Manager(models.Manager):
    use_in_migrations = True

    def create_parsed_payload(self, payload):

        # совершённоедействие и его автор
        self.action = payload['action']
        self.sender_id = payload['sender']['id']
        self.sender_login = payload['sender']['login']

        # поля issue
        self.issue_title = payload['issue']['title']
        self.issue_body = payload['issue']['body']

        # автор issue
        self.issue_author_id = payload['issue']['user']['id']
        self.issue_author_login = payload['issue']['user']['login']

        # идентификаторы (для связи и логов)
        self.issue_id =payload['issue']['id']
        self.repos_id = payload['repository']['id']
        self.issue_number = payload['issue']['number']

        # ссылка на issue (для фразы бота и логов)
        self.issue_url = payload['issue']['html_url']

        if (payload['action'] == 'labeled' or payload['action'] == 'delabeled'):
            self.issue_label = payload['issue']['labels']

        self.save()
        return self

    def get_by_natural_key(self, id):
        return self.get(id=id)

class Payload_GH(models.Model):

    # совершённоедействие и его автор
    action = models.TextField(blank=1)
    sender_id = models.TextField(blank=1)
    sender_login = models.TextField(blank=1)

    # поля issue
    issue_title = models.TextField(blank=1)
    issue_body = models.TextField(blank=1)

    #автор issue
    issue_author_id = models.IntegerField(blank=1, null=1)
    issue_author_login = models.TextField(blank=1)

    # идентификаторы (для связи и логов)
    issue_id = models.IntegerField(blank=1, null=1)
    repos_id = models.IntegerField(blank=1, null=1)
    issue_number = models.IntegerField(blank=1, null=1)

    # ссылка на issue (для фразы бота и логов)
    issue_url = models.TextField(blank=1)

    issue_label = models.TextField(blank=1)


    db_table = 'payloads_from_gh'
    objects = Payload_GH_Manager()

    class Meta:
        verbose_name = 'payload_from_gh'
        verbose_name_plural = 'payloads_from_gh'


# ======================================================= REDMINE ======================================================


''' Класс "Payload_RM" - payload-ы с редмайна '''
class Payload_RM_Manager(models.Manager):
    use_in_migrations = True

    def create_parsed_payload(self, payload):

        payload = payload['payload']  # достаём содержимое payload. payload payload. payload? payload!

        # совершённое действие
        self.action = payload['action']

        # автор issue
        self.issue_author_id = payload['issue']['author']['id']
        self.issue_author_login = payload['issue']['author']['login']
        self.issue_author_firstname = payload['issue']['author']['firstname']
        self.issue_author_lastname = payload['issue']['author']['lastname']

        # при update возможна добавка комментария
        if (payload['action'] == 'updated'):
            # тело комментария
            self.comment_body = payload['journal']['notes']

            # id комментария (для связи и логов)
            self.comment_id = payload['journal']['id']

            # автор комментария
            self.comment_author_id = payload['journal']['author']['id']
            self.comment_author_login = payload['journal']['author']['login']
            self.comment_author_firstname = payload['journal']['author']['firstname']
            self.comment_author_lastname = payload['journal']['author']['lastname']

        # поля issue
        self.issue_title = payload['issue']['subject']
        self.issue_body = payload['issue']['description']
        self.tracker_id = payload['issue']['tracker']['id']
        self.status_id = payload['issue']['status']['id']
        self.priority_id = payload['issue']['priority']['id']

        # идентификаторы (для связи и логов)
        self.issue_id = payload['issue']['id']
        self.project_id = payload['issue']['project']['id']

        # ссылка на issue (для фразы бота и логов)
        self.issue_url = payload['url']

        self.save()
        return payload

    def get_by_natural_key(self, id):
        return self.get(id=id)

class Payload_RM(models.Model):

    # совершённое действие
    action = models.TextField(blank=1)

    # автор issue
    issue_author_id = models.IntegerField(blank=1, null=1)
    issue_author_login = models.TextField(blank=1)
    issue_author_firstname = models.TextField(blank=1)
    issue_author_lastname = models.TextField(blank=1)

    # тело комментария
    comment_body = models.TextField(blank=1)

    # id комментария (для связи и логов)
    comment_id = models.IntegerField(blank=1, null=1)

    # автор комментария
    comment_author_id = models.IntegerField(blank=1, null=1)
    comment_author_login = models.TextField(blank=1)
    comment_author_firstname = models.TextField(blank=1)
    comment_author_lastname = models.TextField(blank=1)

    # поля issue
    issue_title = models.TextField(blank=1)
    issue_body = models.TextField(blank=1)
    tracker_id = models.IntegerField(blank=1, null=1)
    status_id = models.IntegerField(blank=1, null=1)
    priority_id = models.IntegerField(blank=1, null=1)

    # идентификаторы (для связи и логов)
    issue_id = models.IntegerField(blank=1, null=1)
    project_id = models.IntegerField(blank=1, null=1)

    # ссылка на issue (для фразы бота и логов)
    issue_url = models.TextField(blank=1)


    db_table = 'payloads_from_rm'
    objects = Payload_RM_Manager()

    class Meta:
        verbose_name = 'payload_from_rm'
        verbose_name_plural = 'payloads_from_rm'


# ==================================================== СВЯЗЬ COMMENTS ==================================================


''' Класс "Linked_Comments" - связанные комментарии в issue (comment_id_rm - comment_id_gh, linked_issues_id) '''
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

    def get_all(self):
        return self.all()

class Linked_Comments(models.Model):

    comment_id_rm = models.IntegerField(blank=1, null=1)     # id комментария в редмайне
    comment_id_gh = models.IntegerField(blank=1, null=1)     # id комментария в гитхабе

    db_table = 'linked_comments'
    objects = Linked_Comments_Manager()

    class Meta:
        verbose_name = 'linked_comments'
        verbose_name_plural = 'linked_comments'


# ===================================================== СВЯЗЬ ISSUES ===================================================


# TODO: linked_comments - ForeignKey (https://stackoverflow.com/questions/3937194/django-cascade-deletion-in-manytomanyrelation) (?)
''' Класс "Linked_Issues" - связанные issues (issue_id_rm - repo_id_gh, issue_id_gh) '''
class Linked_Issues_Manager(models.Manager):
    use_in_migrations = True

    def create_linked_issues(self, issue_id_rm, issue_id_gh, repos_id_gh, issue_num_gh,
                             tracker_id_rm, status_id_rm, priority_id_rm, is_opened):
        linked_issues = self.model(issue_id_rm=issue_id_rm,
                                   issue_id_gh=issue_id_gh,
                                   repos_id_gh=repos_id_gh,
                                   issue_num_gh=issue_num_gh,
                                   tracker_id_rm=tracker_id_rm,
                                   status_id_rm=status_id_rm,
                                   priority_id_rm=priority_id_rm,
                                   is_opened=is_opened)
        linked_issues.save()  # сохранение linked_issues в базе данных

        return linked_issues

    def get_by_natural_key(self, id):
        return self.get(id=id)

    def get_issue_by_id_rm(self, issue_id_rm):
        return self.filter(issue_id_rm=issue_id_rm)

    def get_issue_by_id_gh(self, issue_id_gh):
        return self.filter(issue_id_gh=issue_id_gh)

    def get_all(self):
        return self.all()

class Linked_Issues(models.Model):
    issue_id_rm = models.IntegerField(blank=1, null=1)           # id issue в редмайне
    issue_id_gh = models.IntegerField(blank=1, null=1)           # id issue в гитхабе

    repos_id_gh = models.IntegerField(blank=1, null=1)           # id репозитория в гитхабе
    issue_num_gh = models.IntegerField(blank=1, null=1)          # номер issue в репозитории гитхаба

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


# TODO: linked_issues - ForeignKey (https://stackoverflow.com/questions/3937194/django-cascade-deletion-in-manytomanyrelation) (?)
''' Класс "Linked_Projects" - связанные projects (project_id_rm - repo_id_gh) '''
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

    def get_project_by_id_rm(self, project_id_rm):
        return self.filter(project_id_rm=project_id_rm)

    def get_project_by_id_gh(self, repos_id_gh):
        return self.filter(repos_id_gh=repos_id_gh)

    def get_linked_projects(self, project_id_rm, repos_id_gh):
        return self.filter(project_id_rm=project_id_rm,
                           repos_id_gh=repos_id_gh)

    def get_all(self):
        return self.all()

class Linked_Projects(models.Model):

    # используются для привязки проектов
    project_id_rm = models.IntegerField(blank=1, null=1)    # id проекта в редмайне
    repos_id_gh = models.IntegerField(blank=1, null=1)      # id репозитория в гитхабе

    # ссылки - используются лишь для получения id проектов, но более удобны лдя человека
    url_rm = models.TextField(blank=1)                      # ссылка на проект в редмайне
    url_gh = models.TextField(blank=1)                      # ссылка на проект в гитхабе

    issues = models.ManyToManyField(Linked_Issues, blank=1) # задачи в проекте

    # время последней связи используется для повторной привязки проектов
    #last_link_time = models.DateTimeField(default=datetime.datetime.today())
    last_link_time = models.DateTimeField(default=timezone.now)

    def add_linked_issues(self, linked_issues):

        self.issues.add(linked_issues)

        return linked_issues


    def get_issue_by_id_gh(self, issue_id_gh):
        return Linked_Issues.objects.get_issue_by_id_gh(issue_id_gh)

    def get_issue_by_id_rm(self, issue_by_id_rm):
        return Linked_Issues.objects.get_issue_by_id_rm(issue_by_id_rm)
    
    
    db_table = 'linked_projects'
    objects = Linked_Projects_Manager()

    class Meta:
        verbose_name = 'linked_projects'
        verbose_name_plural = 'linked_projects'
