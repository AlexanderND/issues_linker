from collections import deque                           # двухсторонняя очередь в питоне

from django.db import models

from issues_linker.my_functions import WRITE_LOG        # ведение логов

from django.core.exceptions import ObjectDoesNotExist   # обработка исключений: объект не найден

# обработка payload-ов
from issues_linker.process_payload_from_gh import process_payload_from_gh    # обработка запроса гитхаба
from issues_linker.process_payload_from_rm import process_payload_from_rm    # обработка запроса редмайна
# загрузка комментариев к issue в Github
from issues_linker.process_comment_payload_from_gh import process_comment_payload_from_gh
# связь проектов
from issues_linker.link_projects import link_projects

import threading    # многопоточность
import time         # задержка


# ================================================ ОЧЕРЕДЬ ОБРАБОТКИ ЗАДАЧ =============================================


''' Класс "Tasks_In_Queue" - задача в очереди обработки задач '''
class Task_In_Queue():

    def __init__(self, payload, type):

        self.payload = payload

        ''' 1 - link_projects '''
        ''' 2 - process_payload_from_rm '''
        ''' 3 - process_payload_from_gh '''
        ''' 4 - process_comment_payload_from_gh '''
        self.type = type

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


    def get_all(self):

        tasks_queue = self.all()

        if (len(tasks_queue) < 1):
            tasks_queue = None

        else:
            tasks_queue = tasks_queue[0]

        return tasks_queue

class Tasks_Queue(models.Model):

    tasks_queue = deque()   # очередь задач

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

    def tasks_queue_daemon(self, sleep_retry):
        retry_wait = 0

        # продолжаем брать задачи из очереди, пока есть задачи
        while (len(self.tasks_queue) > 0):

            payload = self.tasks_queue[0].payload
            type = self.tasks_queue[0].type

            try:
                process_result = self.process_payload(payload, type)

                # определяем результат обработки
                if (process_result.status_code == 200 or process_result.status_code == 201):

                    retry_wait = 0  # сброс времени ожидания перед повторным запуском

                    self.tasks_queue.popleft()  # удаляем задачу из очереди
                    self.save()                 # обновление tasks_queue в базе данных

                else:
                    retry_wait += sleep_retry   # увеличение времени ожидания (чтобы не перегружать сервер)
            except:
                retry_wait += sleep_retry       # увеличение времени ожидания (чтобы не перегружать сервер)
                pass

            time.sleep(retry_wait)  # ждём перед следующим запуском

    def put_in_queue(self, payload, type):

        # создаём задачу на обработку
        task_in_queue = Task_In_Queue(payload, type)
        self.tasks_queue.append(task_in_queue)  # добавляем задачу в очередь обработки
        self.save()                             # обновление tasks_queue в базе данных

        # запускаем демона, отчищающего очередь, если в очереди только 1 элемент (только что добавили)
        if (len(self.tasks_queue) == 1):
            sleep_retry = 2
            daemon = threading.Thread(target=self.tasks_queue_daemon,
                                      args=(sleep_retry,),
                                      daemon=True)
            daemon.start()


    # ЗАГРУЗКА ОЧЕРЕДИ (если не создана - создаём, если создана - отправляем)
    @classmethod
    def load(self):

        queue = self.objects.get_all()

        if (queue == None):
            queue = Tasks_Queue.objects.create_tasks_queue()

        return queue


    db_table = 'tasks_queue'
    objects = Tasks_Queue_Manager()

    class Meta:
        verbose_name = 'tasks_queues'
        verbose_name_plural = 'tasks_queue'