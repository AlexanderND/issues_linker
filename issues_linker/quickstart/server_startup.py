from issues_linker.my_functions import WRITE_LOG        # ведение логов

import datetime

from issues_linker.link_projects import relink_projects
from issues_linker.link_projects import link_projects

# константы сервера
from issues_linker.my_functions import allow_log, allow_log_file, allow_log_cyclic, allow_log_project_linking,\
    detailed_log_project_linking, allow_correct_github_labels, allow_projects_relinking, allow_queue_daemon_restarting,\
    allow_issues_post_rm_to_gh, BOT_ID_RM, BOT_ID_GH, tracker_ids_rm, status_ids_rm, priority_ids_rm, url_rm

# мои модели (связь)
from issues_linker.quickstart.models import Linked_Projects, Linked_Issues, Linked_Comments

from issues_linker.quickstart.models_tasks_queue import start_queue_daemon, put_task_in_queue, Tasks_In_Queue


def server_startup():

    def log_server_startup_begin(num_projects, num_issues, num_comments, num_tasks):

        WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
                  'Starting up the server!\n' +
                  'Checking server starus:\n' +
                  'DATABASE       | num_projects:                   ' + str(num_projects) + '\n' +
                  '               | num_issues:                     ' + str(num_issues) + '\n' +
                  '               | num_comments:                   ' + str(num_comments) + '\n' +
                  '               | tasks_in_queue:                 ' + str(num_tasks) + '\n' +
                  '               | --------------------------------' + '\n' +
                  'SERVER_CONFIG  | allow_log:                      ' + str(allow_log) + '\n' +
                  '               | allow_log_file:                 ' + str(allow_log_file) + '\n' +
                  '               | allow_log_cyclic:               ' + str(allow_log_cyclic) + '\n' +
                  '               | allow_log_project_linking:      ' + str(allow_log_project_linking) + '\n' +
                  '               | detailed_log_project_linking:   ' + str(detailed_log_project_linking) + '\n' +
                  '               | allow_correct_github_labels:    ' + str(allow_correct_github_labels) + '\n' +
                  '               | allow_queue_daemon_restarting:  ' + str(allow_queue_daemon_restarting) + '\n' +
                  '               | allow_projects_relinking:       ' + str(allow_projects_relinking) + '\n' +
                  '               | allow_issues_post_rm_to_gh:     ' + str(allow_issues_post_rm_to_gh) + '\n' +
                  '               | BOT_ID_RM:                      ' + str(BOT_ID_RM) + '\n' +
                  '               | BOT_ID_GH:                      ' + str(BOT_ID_GH) + '\n' +
                  '               | tracker_ids_rm:                 ' + str(tracker_ids_rm) + '\n' +
                  '               | status_ids_rm:                  ' + str(status_ids_rm) + '\n' +
                  '               | priority_ids_rm:                ' + str(priority_ids_rm) + '\n' +
                  '               | url_rm:                         ' + str(url_rm) + '\n')


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
