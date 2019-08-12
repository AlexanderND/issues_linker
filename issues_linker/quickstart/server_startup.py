from issues_linker.my_functions import WRITE_LOG        # ведение логов

import datetime

from issues_linker.link_projects import relink_projects
from issues_linker.link_projects import link_projects

# разрешение запуска процесса обновления связи между проектами
from issues_linker.my_functions import allow_projects_relinking

# мои модели (связь)
from issues_linker.quickstart.models import Linked_Projects, Linked_Issues, Linked_Comments

from issues_linker.quickstart.models_tasks_queue import start_queue_daemon

# мои модели (очередь обработки задач)
#from issues_linker.quickstart.models_tasks_queue import Tasks_Queue

def server_startup():

    def log_server_startup_begin(num_projects, num_issues, num_comments):

        WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
                  'Starting up the server!\n' +
                  'Checking db starus:\n' +
                  'PROJECTS  | num_projects:  ' + str(num_projects) + '\n' +
                  'ISSUES    | num_issues:    ' + str(num_issues) + '\n' +
                  'COMMENTS  | num_comments:  ' + str(num_comments) + '\n')


    if (allow_projects_relinking):

        linked_projects = Linked_Projects.objects.get_all()
        linked_issues = Linked_Issues.objects.get_all()
        linked_comments = Linked_Comments.objects.get_all()

        num_projects = len(linked_projects)
        num_issues = len(linked_issues)
        num_comments = len(linked_comments)

        log_server_startup_begin(num_projects, num_issues, num_comments)

        #tasks_queue = Tasks_Queue.load()

        # перезапуск демона очереди
        #tasks_queue.start_queue_daemon()
        start_queue_daemon()

        # отправка в очередь задач на повторную связь проектов
        '''if (len(linked_projects) > 0):
            for linked_projects_ in linked_projects:
                tasks_queue.put_in_queue(linked_projects_, 5)'''

    else:

        WRITE_LOG("WARNING: re-linking projects was canceled due to setting 'allow_projects_relinking = False'\n" +
                  "We can't guarantee that the linked data is up-to-date!\n" +
                  "Please, enable the 'allow_projects_relinking' parameter in 'my_functions'\n")
