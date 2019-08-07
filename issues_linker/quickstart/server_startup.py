from issues_linker.my_functions import WRITE_LOG        # ведение логов

import datetime

from issues_linker.link_projects import relink_projects
from issues_linker.link_projects import link_projects

# разрешение запуска процесса обновления связи между проектами
from issues_linker.my_functions import allow_projects_relinking

def server_startup(tasks_queue, linked_projects, linked_issues, linked_comments):

    num_projects = len(linked_projects)
    num_issues = len(linked_issues)
    num_comments = len(linked_comments)

    def log_server_startup_begin():

        WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
                  'Starting up the server!\n' +
                  'Checking db starus:\n' +
                  'PROJECTS  | num_projects:  ' + str(num_projects) + '\n' +
                  'ISSUES    | num_issues:    ' + str(num_issues) + '\n' +
                  'COMMENTS  | num_comments:  ' + str(num_comments) + '\n')

    log_server_startup_begin()

    if (allow_projects_relinking):

        if (len(linked_projects) > 0):

            WRITE_LOG("re-linking projects in progress...")

            for linked_projects_ in linked_projects:
                tasks_queue.put_in_queue(linked_projects_, 5)

        else:
            WRITE_LOG("there are no projects to re-link!")

    else:

        WRITE_LOG("WARNING: re-linking projects was canceled due to setting 'allow_projects_relinking = False'\n" +
                  "We can't guarantee that the linked data is up-to-date!\n" +
                  "Please, enable the 'allow_projects_relinking' parameter in 'my_functions'\n")
