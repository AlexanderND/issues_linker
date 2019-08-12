from collections import deque                           # двухсторонняя очередь в питоне

from django.db import models

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


def log_process_error(queue, try_count, sleep_time, process_result):

    type = queue[0].type
    queue_len = len(queue)

    if (type == 1):
        action = 'link_projects'
    elif (type == 2):
        action = 'process_payload_from_rm'
    elif (type == 3):
        action = 'process_payload_from_gh'
    else:   # type == 4
        action = 'process_comment_payload_from_gh'

    error_text = 'encountered some process_error'

    WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
              'WARNING: Tried to ' + action + ', but ' + error_text + '\n' +
              ' | queue_len:    ' + str(queue_len) + '\n' +
              ' | try_count:    ' + str(try_count) + '\n' +
              ' | retrying in:  ' + str(sleep_time) + '\n' +
              ' | error_code:   ' + str(process_result.status_code) + '\n' +
              ' | error_text:   ' + str(process_result.text))

def log_connection_refused(queue, try_count, sleep_time):

    type = queue[0].type
    queue_len = len(queue)

    if (type == 1):
        action = 'link_projects'
        error_text = 'REDMINE is not responding'
    elif (type == 2):
        action = 'process_payload_from_rm'
        error_text = 'GITHUB is not responding'
    elif (type == 3):
        action = 'process_payload_from_gh'
        error_text = 'REDMINE is not responding'
    else:   # type == 4
        action = 'process_comment_payload_from_gh'
        error_text = 'REDMINE is not responding'

    WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
              'WARNING: Tried to ' + action + ', but ' + error_text + '\n' +
              ' | queue_len:    ' + str(queue_len) + '\n' +
              ' | try_count:    ' + str(try_count) + '\n' +
              ' | retrying in:  ' + str(sleep_time))


# ================================================ ОЧЕРЕДЬ ОБРАБОТКИ ЗАДАЧ =============================================


"""''' Класс "Tasks_In_Queue" - задача в очереди обработки задач '''
class Task_In_Queue_Manager(models.Manager):
    use_in_migrations = True

    def create_task_in_queue(self, payload, type):

        # определяем тип обработки
        if (type == 1):
            payload_parsed = payload
            task_in_queue = self.model(payload=payload_parsed,
                                       type=type)

        elif (type == 2):
            payload_parsed = Payload_RM.objects.create_parsed_payload(payload)
            task_in_queue = self.model(payload_rm=payload_parsed,
                                       type=type)

        elif (type == 3):
            payload_parsed = Payload_GH.objects.create_parsed_payload(payload)
            task_in_queue = self.model(payload_gh=payload_parsed,
                                       type=type)

        else:  # type == 4
            payload_parsed = Comment_Payload_GH.objects.create_parsed_payload(payload)
            task_in_queue = self.model(comment_payload_gh=payload_parsed,
                                       type=type)


        task_in_queue.save()    # сохранение task_in_queue в бвзе данных
        return task_in_queue

    def get_by_natural_key(self, id):
        return self.get(id=id)

    def get_all(self):

        tasks_in_queue = self.all()

        if (len(tasks_in_queue) < 1):
            tasks_in_queue = None

        return tasks_in_queue

class Task_In_Queue(models.Model):

    # payload комментарии с гитхаба
    comment_payload_gh = models.OneToOneField(
        Comment_Payload_GH,
        on_delete=models.CASCADE,
        default=None)

    # payload с гитхаба
    payload_gh = models.OneToOneField(
        Payload_GH,
        on_delete=models.CASCADE,
        default=None)

    # payload с редмайна
    payload_rm = models.OneToOneField(
        Payload_RM,
        on_delete=models.CASCADE,
        default=None)

    # payload создание связи между проектами
    payload = models.CharField(blank=1, max_length=1024)

    type = models.SmallIntegerField()               # id issue в гитхабе

    db_table = 'tasks_in_queue'
    objects = Task_In_Queue_Manager()

    class Meta:
        verbose_name = 'task_in_queue'
        verbose_name_plural = 'tasks_in_queue'

''' Класс "Tasks_Queue" - очередь обработки задач '''
class Tasks_Queue_Manager(models.Manager):

    use_in_migrations = True


    def create_tasks_queue(self):

        tasks_queue = self.model()
        tasks_queue.save()      # сохранение tasks_queue в базе данных

        return tasks_queue

    def update_tasks_queue(self):

        self.save()             # сохранение tasks_queue в базе данных
        return self

    def get_queue(self):

        tasks_queue = self.all()

        if (len(tasks_queue) < 1):
            return None

        elif (len(tasks_queue) > 1):
            for i in range(len(tasks_queue)):
                tasks_queue[i].delete()

            return None

        return tasks_queue[0]

class Tasks_Queue(models.Model):

    tasks_in_queue = models.ManyToManyField(Task_In_Queue, blank=1)
    

    def tasks_queue_daemon(self, sleep_retry):
        WRITE_LOG('daemon')
        retry_wait = 0

        # продолжаем брать задачи из очереди, пока есть задачи
        tasks = Task_In_Queue.objects.get_all()
        while (tasks != None):

            payload = tasks[0].payload
            type = tasks[0].type

            try:
                process_result = self.process_payload(payload, type)

                # определяем результат обработки
                if (process_result.status_code == 200 or process_result.status_code == 201):

                    retry_wait = 0      # сброс времени ожидания перед повторным запуском

                    tasks[0].delete()   # удаляем задачу из очереди

                else:
                    retry_wait += sleep_retry   # увеличение времени ожидания (чтобы не перегружать сервер)

            # пропускаем ошибку 'database is locked'
            except OperationalError:
                retry_wait += sleep_retry       # увеличение времени ожидания (чтобы не перегружать сервер)
                pass

            tasks = Task_In_Queue.objects.get_all()
            time.sleep(retry_wait)  # ждём перед следующим запуском

    def start_queue_daemon(self):
        sleep_retry = 2
        daemon = threading.Thread(target=self.tasks_queue_daemon,
                                  args=(sleep_retry,),
                                  daemon=True)
        daemon.start()


    def process_payload(self, payload, type):

        # определяем тип обработки
        if (type == 1):
            process_result = link_projects(payload)

        elif (type == 2):
            process_result = process_payload_from_rm(payload)

        elif (type == 3):
            process_result = process_payload_from_gh(payload)

        else:  # type == 4
            process_result = process_comment_payload_from_gh(payload)

        return process_result

    def put_in_queue(self, payload, type):

        # создаём задачу на обработку в базе данных
        task_in_queue = Task_In_Queue.objects.create_task_in_queue(
            payload,
            type)

        while True:
            try:
                self.tasks_in_queue.add(task_in_queue)

                # запускаем демона, отчищающего очередь, если в очереди только 1 элемент (только что добавили)
                tasks = Task_In_Queue.objects.get_all()
                if (len(tasks) == 1):
                    self.start_queue_daemon()

                break   # выходим из цикла

            # пропускаем ошибку 'database is locked'
            except OperationalError:
                #time.sleep(0.02)
                pass

        return task_in_queue


    # ЗАГРУЗКА ОЧЕРЕДИ (если не создана - создаём, если создана - отправляем)
    @classmethod
    def load(self):

        queue = self.objects.get_queue()

        if (queue == None):
            queue = Tasks_Queue.objects.create_tasks_queue()

        return queue


    db_table = 'tasks_queue'
    objects = Tasks_Queue_Manager()

    class Meta:
        verbose_name = 'tasks_queues'
        verbose_name_plural = 'tasks_queue'"""

# TODO: заменить type с
''' Класс "Tasks_In_Queue" - задача в очереди обработки задач '''
class Task_In_Queue():

    def __init__(self, payload, payload_type):
        self.payload = payload
        #WRITE_LOG(type(payload))
        #WRITE_LOG(type(payload_type))

        ''' 1 - link_projects '''
        ''' 2 - process_payload_from_rm '''
        ''' 3 - process_payload_from_gh '''
        ''' 4 - process_comment_payload_from_gh '''
        ''' 5 - relink_projects '''
        self.type = payload_type

''' Класс "Tasks_Queue" - очередь обработки задач '''
class Tasks_Queue_Manager(models.Manager):
    use_in_migrations = True

    def create_tasks_queue(self):

        tasks_queue = self.model()
        tasks_queue.save()  # сохранение tasks_queue в базе данных

        return tasks_queue

    def get_queue(self):

        tasks_queue = self.all()

        if (len(tasks_queue) < 1):
            return None

        elif (len(tasks_queue) > 1):
            for i in range(len(tasks_queue)):
                tasks_queue[i].delete()

            return None

        return tasks_queue[0]

class Tasks_Queue(models.Model):

    queue = deque()

    def tasks_queue_daemon(self, sleep_retry):

        retry_wait = 0
        try_count = 0

        # продолжаем брать задачи из очереди, пока есть задачи
        while (len(self.queue) > 0):

            payload = self.queue[0].payload
            type = self.queue[0].type

            try:
                process_result = self.process_payload(payload, type)

                # определяем результат обработки
                if (process_result.status_code == 200 or process_result.status_code == 201):

                    retry_wait = 0          # сброс времени ожидания перед повторным запуском
                    try_count = 0           # сброс счётчика попыток

                    self.queue.popleft()    # удаляем задачу из очереди

                else:

                    retry_wait += sleep_retry   # увеличение времени ожидания (чтобы не перегружать сервер)

                    try_count += 1
                    log_process_error(self.queue, try_count, retry_wait, process_result)

            # пропускаем ошибку 'database is locked'
            except OperationalError:
                time.sleep(0.02)    # ждём перед следующим запуском
                continue

            # пропускаем ошибку 'Connection refused' (сервер упал)
            except RequestException:

                retry_wait += sleep_retry   # увеличение времени ожидания (чтобы не перегружать сервер)

                try_count += 1
                log_connection_refused(self.queue, try_count, retry_wait)

                pass

            time.sleep(retry_wait)  # ждём перед следующим запуском

    def start_queue_daemon(self):
        sleep_retry = 2
        daemon = threading.Thread(target=self.tasks_queue_daemon,
                                  args=(sleep_retry,),
                                  daemon=True)
        daemon.start()

    def process_payload(self, payload, type):

        # определяем тип обработки
        if (type == 1):
            process_result = link_projects(payload)

        elif (type == 2):
            process_result = process_payload_from_rm(payload)

        elif (type == 3):
            process_result = process_payload_from_gh(payload)

        elif (type == 4):
            process_result = process_comment_payload_from_gh(payload)

        else:  # type == 5
            process_result = relink_projects(payload)

        return process_result

    def put_in_queue(self, payload, type):

        # создаём задачу на обработку в базе данных
        task_in_queue = Task_In_Queue(payload, type)

        while True:
            try:
                self.queue.append(task_in_queue)

                # запускаем демона, отчищающего очередь, если в очереди только 1 элемент (только что добавили)
                if (len(self.queue) == 1):
                    self.start_queue_daemon()

                break  # выходим из цикла

            # пропускаем ошибку 'database is locked'
            except OperationalError:
                time.sleep(0.02)    # ждём перед следующим запуском
                continue

        return task_in_queue

    # ЗАГРУЗКА ОЧЕРЕДИ (если не создана - создаём, если создана - отправляем)
    @classmethod
    def load(self):

        queue = self.objects.get_queue()

        if (queue == None):
            queue = Tasks_Queue.objects.create_tasks_queue()

        return queue

    db_table = 'tasks_queue'
    objects = Tasks_Queue_Manager()

    class Meta:
        verbose_name = 'tasks_queues'
        verbose_name_plural = 'tasks_queue'