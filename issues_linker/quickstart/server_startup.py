from issues_linker.my_functions import WRITE_LOG        # ведение логов

import datetime

from issues_linker.link_projects import relink_projects
from issues_linker.link_projects import link_projects

# разрешение запуска процесса обновления связи между проектами
from issues_linker.my_functions import allow_projects_relinking, allow_queue_daemon_restarting

# мои модели (связь)
from issues_linker.quickstart.models import Linked_Projects, Linked_Issues, Linked_Comments

from issues_linker.quickstart.models_tasks_queue import start_queue_daemon, put_task_in_queue, Tasks_In_Queue


def server_startup():

    def log_server_startup_begin(num_projects, num_issues, num_comments, num_tasks):

        WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
                  'Starting up the server!\n' +
                  'Checking db starus:\n' +
                  'PROJECTS  | num_projects:  ' + str(num_projects) + '\n' +
                  'ISSUES    | num_issues:    ' + str(num_issues) + '\n' +
                  'COMMENTS  | num_comments:  ' + str(num_comments) + '\n' +
                  'QUEUE     | num_tasks:     ' + str(num_tasks) + '\n')


    if (allow_queue_daemon_restarting):

        linked_projects = Linked_Projects.objects.get_all()
        linked_issues = Linked_Issues.objects.get_all()
        linked_comments = Linked_Comments.objects.get_all()
        queue = Tasks_In_Queue

        num_projects = len(linked_projects)
        num_issues = len(linked_issues)
        num_comments = len(linked_comments)
        num_tasks = queue.objects.get_queue_len()

        log_server_startup_begin(num_projects, num_issues, num_comments, num_tasks)

        # перезапуск демона очереди
        if (num_tasks > 0):
            WRITE_LOG('Restarting queue daemon...\n')
            start_queue_daemon()

        if (allow_projects_relinking):

            # отправка в очередь задачи на повторную связь проектов
            if (num_projects > 0):
                put_task_in_queue('', 5)

        else:
            WRITE_LOG("WARNING: re-linking projects was canceled due to setting 'allow_projects_relinking = False'\n" +
                      "We can't guarantee that the linked data is up-to-date!\n" +
                      "Please, enable the 'allow_projects_relinking' parameter in 'my_functions'\n")

    else:
        WRITE_LOG("WARNING: restarting queue_daemon was canceled due to setting 'allow_queue_daemon_restarting = False'\n" +
                  "(re-linking projects was also canceled)\n" +
                  "Please, enable the 'allow_queue_daemon_restarting' parameter in 'my_functions'\n")
