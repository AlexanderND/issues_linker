from collections import deque                           # двухсторонняя очередь в питоне

from django.db import models
import json

from issues_linker.my_functions import WRITE_LOG        # ведение логов
from issues_linker.my_functions import WRITE_LOG_WAR    # ведение логов (предупреждения)

from django.core.exceptions import ObjectDoesNotExist   # обработка исключений: объект не найден

# обработка payload-ов
from issues_linker.process_payload_from_gh import process_payload_from_gh    # обработка запроса гитхаба
from issues_linker.process_payload_from_rm import process_payload_from_rm    # обработка запроса редмайна
# загрузка комментариев к issue в Github
from issues_linker.process_comment_payload_from_gh import process_comment_payload_from_gh

# связь проектов
from issues_linker.link_projects import link_projects
from issues_linker.link_projects import relink_projects

import threading    # многопоточность
import time         # задержка

from django.db.utils import OperationalError
from requests.exceptions import RequestException

import datetime

# мои модели (хранение на сервере)
from issues_linker.quickstart.models import Comment_Payload_GH, Payload_GH, Payload_RM

# мои модели (связь)
from issues_linker.quickstart.models import Linked_Projects


def log_process_error(queue, try_count, sleep_time, process_result):

    first_task = queue.objects.peekleft()
    type = first_task.process_type
    queue_len = queue.objects.get_queue_len()

    if (type == 1):
        action = 'link_projects'
    elif (type == 2):
        action = 'process_payload_from_rm'
    elif (type == 3):
        action = 'process_payload_from_gh'
    elif (type == 4):
        action = 'process_comment_payload_from_gh'
    else:   # type == 5
        action = 'relink_projects'

    error_text = 'encountered some internal server error (process_error)'

    WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
              'WARNING: Tried to ' + action + ', but ' + error_text + '\n' +
              ' | queue_len:    ' + str(queue_len) + '\n' +
              ' | try_count:    ' + str(try_count) + '\n' +
              ' | retrying in:  ' + str(sleep_time) + '\n' +
              ' | error_code:   ' + str(process_result.status_code) + '\n' +
              ' | error_text:   ' + str(process_result.text) + '\n')

def log_connection_refused(queue, try_count, sleep_time):

    first_task = queue.objects.peekleft()
    type = first_task.process_type
    queue_len = queue.objects.get_queue_len()

    if (type == 1):
        action = 'link_projects'
        error_text = 'REDMINE is not responding'
    elif (type == 2):
        action = 'process_payload_from_rm'
        error_text = 'GITHUB is not responding'
    elif (type == 3):
        action = 'process_payload_from_gh'
        error_text = 'REDMINE is not responding'
    elif (type == 4):
        action = 'process_comment_payload_from_gh'
        error_text = 'REDMINE is not responding'
    else:   # type == 5
        action = 'relink_projects'
        error_text = 'REDMINE is not responding'

    WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
              'WARNING: Tried to ' + action + ', but ' + error_text + '\n' +
              ' | queue_len:    ' + str(queue_len) + '\n' +
              ' | try_count:    ' + str(try_count) + '\n' +
              ' | retrying in:  ' + str(sleep_time) + '\n')


# ================================================ ОЧЕРЕДЬ ОБРАБОТКИ ЗАДАЧ =============================================


''' Класс "Task_In_Queue" - задачи очереди обработки задач '''
class Tasks_In_Queue_Manager(models.Manager):
    use_in_migrations = True

    def create_task_in_queue(self, item, process_type):

        payload_parced = json.dumps(item)
        task_in_queue = self.model(payload=payload_parced,
                                   process_type=process_type)

        task_in_queue.save()    # сохранение task_in_queue в бвзе данных
        return task_in_queue

    def get_by_natural_key(self, id):
        return self.filter(id=id)


    def get_queue_len(self):
        tasks_in_queue = self.all()
        queue_len = len(tasks_in_queue)
        return queue_len

    def get_all(self):

        tasks_in_queue = self.all()

        if (len(tasks_in_queue) < 1):
            tasks_in_queue = None

        return tasks_in_queue

    def get_first_task(self):

        tasks_in_queue = self.get_all()

        if (tasks_in_queue != None):
            first_task = tasks_in_queue[0]

            for i in range(len(tasks_in_queue)):
                if (tasks_in_queue[i].id < first_task.id):
                    first_task = tasks_in_queue[i]

            return first_task

        else:
            return None


    def append(self, payload, process_type):
        task_in_queue = self.create_task_in_queue(payload, process_type)
        return task_in_queue

    def popleft(self):
        first_task = self.get_first_task()
        first_task.delete()

    def peekleft(self):
        first_task = self.get_first_task()
        return first_task

class Tasks_In_Queue(models.Model):

    payload = models.TextField(blank=1)

    ''' 1 - link_projects '''
    ''' 2 - process_payload_from_rm '''
    ''' 3 - process_payload_from_gh '''
    ''' 4 - process_comment_payload_from_gh '''
    ''' 5 - relink_projects '''
    process_type = models.IntegerField(blank=1, null=1)

    db_table = 'tasks_in_queue'
    objects = Tasks_In_Queue_Manager()

    class Meta:
        verbose_name = 'tasks_in_queue'
        verbose_name_plural = 'tasks_in_queue'


def tasks_queue_daemon(sleep_retry):

    queue = Tasks_In_Queue

    retry_wait = 0
    try_count = 0

    # продолжаем брать задачи из очереди, пока есть задачи
    while (queue.objects.get_queue_len() > 0):

        first_task = queue.objects.peekleft()
        payload = json.loads(first_task.payload)
        process_type = first_task.process_type

        try:
            process_result = process_payload(payload, process_type)

            # определяем результат обработки
            if (process_result.status_code == 200 or process_result.status_code == 201):

                retry_wait = 0          # сброс времени ожидания перед повторным запуском
                try_count = 0           # сброс счётчика попыток

                queue.objects.popleft() # удаляем задачу из очереди

            else:

                retry_wait += sleep_retry  # увеличение времени ожидания (чтобы не перегружать сервер)

                try_count += 1
                log_process_error(queue, try_count, retry_wait, process_result)

        # пропускаем ошибку 'database is locked'
        except OperationalError:
            time.sleep(0.02)  # ждём перед следующим запуском
            continue

        # пропускаем ошибку 'Connection refused' (сервер упал)
        except RequestException:

            retry_wait += sleep_retry  # увеличение времени ожидания (чтобы не перегружать сервер)

            try_count += 1
            log_connection_refused(queue, try_count, retry_wait)

            pass

        time.sleep(retry_wait)  # ждём перед следующим запуском

def start_queue_daemon():
    sleep_retry = 2
    daemon = threading.Thread(target=tasks_queue_daemon,
                              args=(sleep_retry,),
                              daemon=True)
    daemon.start()

def process_payload(payload, process_type):
    # определяем тип обработки
    if (process_type == 1):
        process_result = link_projects(payload)

    elif (process_type == 2):
        process_result = process_payload_from_rm(payload)

    elif (process_type == 3):
        process_result = process_payload_from_gh(payload)

    elif (process_type == 4):
        process_result = process_comment_payload_from_gh(payload)

    else:  # process_type == 5
        process_result = relink_projects()

    return process_result

def put_task_in_queue(payload, process_type):
    queue = Tasks_In_Queue

    while True:
        # обработка ошибка 'database is locked'
        try:

            # создаём задачу на обработку в базе данных
            task_in_queue = queue.objects.append(payload, process_type)

            # запускаем демона, отчищающего очередь, если в очереди только 1 элемент (только что добавили)
            if (queue.objects.get_queue_len() == 1):
                start_queue_daemon()

            break  # выходим из цикла

        except OperationalError:
            time.sleep(0.02)  # ждём перед следующим запуском
            continue
