import os
import datetime
import json

from django.http import HttpResponse    # ответы серверу

from collections import deque           # двухсторонняя очередь в питоне

#from issues_linker.quickstart.models import Linked_Issues, Linked_Comments


# чтение файла
def read_file(file_path):
    # получение абсолютного пути до файла
    script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in

    file_path_absolute = os.path.join(script_dir, file_path)
    file_contents = open(file_path_absolute, 'r').read()    # загрузка данных из файла в строку

    return file_contents

server_config = read_file('server_config.json')
server_config = json.loads(server_config)

def configure_server_constant_bool(constant_name):

    if (server_config[constant_name] == 'True'):
        constant_bool = True

    else:
        constant_bool = False
    return constant_bool

def configure_server_constant_int(constant_name):

    constant_int = int(server_config[constant_name])
    return constant_int

def configure_server_constant_list(constant_name):

    constant_list = server_config[constant_name]
    return constant_list

def configure_server_constant_char(constant_name):

    constant_char = server_config[constant_name]
    return constant_char


# =================================================== КОНСТАНТЫ СЕРВЕРА ================================================


# константы запрета ведения логов
allow_log = configure_server_constant_bool('allow_log')
allow_log_file = configure_server_constant_bool('allow_log_file')
allow_log_cyclic = configure_server_constant_bool('allow_log_cyclic')

allow_log_project_linking = configure_server_constant_bool('allow_log_project_linking')
detailed_log_project_linking = configure_server_constant_bool('detailed_log_project_linking')

# TODO: не транслировать в редмайн и не сохранять на сервере изменения трекера
allow_correct_github_labels = configure_server_constant_bool('allow_correct_github_labels')

# установить False для пересоздания базы данных
allow_queue_daemon_restarting = configure_server_constant_bool('allow_queue_daemon_restarting')
allow_projects_relinking = configure_server_constant_bool('allow_projects_relinking')

allow_issues_post_rm_to_gh = configure_server_constant_bool('allow_issues_post_rm_to_gh')

# id бота в редмайне (предотвращение зацикливания)
BOT_ID_RM = configure_server_constant_int('BOT_ID_RM')

# id бота в гитхабе (предотвращение зацикливания)
BOT_ID_GH = configure_server_constant_int('BOT_ID_GH')

allowed_ips = configure_server_constant_list('allowed_ips')
secret_gh = configure_server_constant_char('secret_gh')


# ===================================================== СПЕЦ. ФУНКЦИИ ==================================================


''' Различные цвета (форматы) текста в консоли '''
'''
HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'
'''

def WRITE_LOG_COLOUR(string, colour):

    if (not allow_log):
        return 0

    if (not allow_log_file):
        print(colour + string + '\033[0m')  # лог в консоли

    else:

        # получение абсолютного пути до файла
        script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
        log_file_name = os.path.join(script_dir, 'logs/server_log.txt')
        log = open(log_file_name, 'a')

        print(colour + string + '\033[0m')  # лог в консоли
        log.write(string + '\n')            # лог в файл

        log.close()

# выбирает цвет автоматически
# TODO: заменить .find на использование разных функций логов (после завершиния разработки?)
def WRITE_LOG(string):

    string = str(string)

    if (string.find('ERROR:') == -1):

        if (string.find('WARNING:') == -1):

            WRITE_LOG_COLOUR(string, '\033[96m')    # выводим в консоли голубым цветом

        else:

            WRITE_LOG_COLOUR(string, '\033[93m')    # выводим в консоли жёлтым цветом

    else:

        WRITE_LOG_COLOUR(string, '\033[91m')        # выводим в консоли красным цветом

# ошибки
def WRITE_LOG_ERR(string):

    string = str(string)

    WRITE_LOG_COLOUR(string, '\033[91m')            # выводим в консоли красным цветом

# предупреждения
def WRITE_LOG_WAR(string):

    string = str(string)

    WRITE_LOG_COLOUR(string, '\033[93m')            # выводим в консоли оранжевым цветом

# уведомления о последующих многократных действиях
def WRITE_LOG_GRN(string):

    string = str(string)

    WRITE_LOG_COLOUR(string, '\033[92m')            # выводим в консоли оранжевым цветом


# обработка спец. символов (\ -> \\)
def align_special_symbols(str):

    str = str.replace('\r\n', '\n')     # для гитхаба

    str = str.replace(r'"', r'\"')      # r - строка без спец. символов
    str = str.replace('\r', '\\r')
    str = str.replace('\n', '\\n')
    str = str.replace('\t', '\\t')

    return str

# удаление фразы бота из текста
def del_bot_phrase(body):

    body_parts = body.split(': ')  # разбиваем body на части (часть 0 - фраза бота)

    # если body пустой - значит, фраза бота закончилась на точку (нет опсания)
    body_processed = ''
    if (len(body_parts) > 1):

        for body_part in range(1, len(body_parts)):
            body_processed += body_parts[body_part]

            # много частей, если пользователь использовал ': ' в тексте
            if (body_part < len(body_parts) - 1):
                body_processed += ': '

        body_processed = body_processed.replace('\n>', '\n')  # убираем цитирование бота

    return body_processed

# создание корректного ответа серверу
def align_request_result(request_result):

    # type() возвращает тип объекта
    if (type(request_result) is HttpResponse):
        return request_result

    else:
        request_result = HttpResponse(request_result.text, status=request_result.status_code)
        return request_result


# функция сопостовления label-а в гитхабе редмайну
def match_label_to_rm(label_gh):

    label = {}

    if (label_gh == 'Priority: low'):
        label['type'] = 'Priority'
        label['id_rm'] = priority_ids_rm[1]

    elif (label_gh == 'Priority: normal'):
        label['type'] = 'Priority'
        label['id_rm'] = priority_ids_rm[0]

    elif (label_gh == 'Priority: urgent'):
        label['type'] = 'Priority'
        label['id_rm'] = priority_ids_rm[2]

    elif (label_gh == 'Status: new'):
        label['type'] = 'Status'
        label['id_rm'] = status_ids_rm[0]

    elif (label_gh == 'Status: working'):
        label['type'] = 'Status'
        label['id_rm'] = status_ids_rm[1]

    elif (label_gh == 'Status: feedback'):
        label['type'] = 'Status'
        label['id_rm'] = status_ids_rm[2]

    elif (label_gh == 'Status: verification'):
        label['type'] = 'Status'
        label['id_rm'] = status_ids_rm[3]

    elif (label_gh == 'Status: rejected'):
        label['type'] = 'Status'
        label['id_rm'] = status_ids_rm[4]

    elif (label_gh == 'Tracker: task'):
        label['type'] = 'Tracker'
        label['id_rm'] = tracker_ids_rm[0]

    elif (label_gh == 'Tracker: bug'):
        label['type'] = 'Tracker'
        label['id_rm'] = tracker_ids_rm[1]

    else:
        WRITE_LOG('ERROR: UNKNOWN GITHUB LABEL: ' + str(label_gh))
        label = None

    return label


# функция сопостовления статуса в редмайне label-у гитхаба
def match_tracker_to_gh(tracker_id_rm):

    if (tracker_id_rm == tracker_ids_rm[0]):
        label_gh = 'Tracker: task'

    elif (tracker_id_rm == tracker_ids_rm[1]):
        label_gh = 'Tracker: bug'

    else:
        WRITE_LOG('ERROR: UNKNOWN REDMINE TRACKER: ' + str(tracker_id_rm))
        label_gh = None

    return label_gh

# функция сопостовления статуса в редмайне label-у гитхаба
def match_status_to_gh(status_id_rm):

    if (status_id_rm == status_ids_rm[0]):
        label_gh = 'Status: new'

    elif (status_id_rm == status_ids_rm[1]):
        label_gh = 'Status: working'

    elif (status_id_rm == status_ids_rm[2]):
        label_gh = 'Status: feedback'

    elif (status_id_rm == status_ids_rm[3]):
        label_gh = 'Status: verification'

    elif (status_id_rm == status_ids_rm[4]):
        label_gh = 'Status: rejected'

    elif (status_id_rm == status_ids_rm[5]):
        label_gh = 'Status: closed'

    else:
        WRITE_LOG('ERROR: UNKNOWN REDMINE STATUS: ' + str(status_id_rm))
        label_gh = None

    return label_gh

# функция сопостовления статуса в редмайне label-у гитхаба
def match_priority_to_gh(priority_id_rm):

    if (priority_id_rm == priority_ids_rm[0]):
        label_gh = 'Priority: normal'

    elif (priority_id_rm == priority_ids_rm[1]):
        label_gh = 'Priority: low'

    elif (priority_id_rm == priority_ids_rm[2]):
        label_gh = 'Priority: urgent'

    else:
        WRITE_LOG('ERROR: UNKNOWN REDMINE PRIORITY: ' + str(priority_id_rm))
        label_gh = None

    return label_gh


# ======================================================== REDMINE =====================================================


# ----------------------------------------------------- КОНСТАНТЫ ------------------------------------------------

'''
-------------------------------- локальный сервер ------------------------------

0 (4)  - Задача                         | Tracker: task
1 (5)  - Ошибка                         | Tracker: bug

--------------------------------- реальный сервер ------------------------------

0 (3) - Задача                          | Tracker: task
1 (1) - Ошибка                          | Tracker: bug
'''
tracker_ids_rm = configure_server_constant_list('tracker_ids_rm')

'''
-------------------------------- локальный сервер ------------------------------

0 (7)  - Новый                          | Status: new
1 (8)  - Выполнение: в работе           | Status: working
2 (9)  - Выполнение: обратная связь     | Status: feedback
3 (10) - Выполнение: проверка           | Status: verification
4 (11) - Отказ                          | Status: rejected
5 (12) - Закрыт                         | Status: closed

--------------------------------- реальный сервер ------------------------------

0 (1) - Новый                           | Status: new
1 (2) - Выполнение: в работе            | Status: working
2 (4) - Выполнение: обратная связь      | Status: feedback
3 (7) - Выполнение: проверка            | Status: verification
4 (6) - Отказ                           | Status: rejected
5 (5) - Закрыт                          | Status: closed
'''
status_ids_rm = configure_server_constant_list('status_ids_rm')

'''
-------------------------------- локальный сервер ------------------------------

0 (11) - Нормальный                     | Priority: normal
1 (10) - Низкий                         | Priority: low
2 (12) - Высокий                        | Priority: urgent

--------------------------------- реальный сервер ------------------------------

0 (4) - Нормальный                      | Priority: normal
1 (3) - Низкий                          | Priority: low
2 (5) - Высокий                         | Priority: urgent
'''
priority_ids_rm = configure_server_constant_list('priority_ids_rm')

# "http://localhost:3000/issues.json"               локальный сервер
# "https://redmine.redsolution.ru/issues.json"      реальный сервер
url_rm = configure_server_constant_char('url_rm')

# ----------------------------------------------------- ФУНКЦИИ --------------------------------------------------

def chk_if_rm_user_is_our_bot(user_id_rm):

    if (user_id_rm == BOT_ID_RM):
        return True
    else:
        return False


def log_issue_post_rm(result, issue, linked_issues):

    action_gh = 'POST'
    repos_id_gh = linked_issues.repos_id_gh
    url_gh = make_gh_repos_url(repos_id_gh)

    WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
              'received webhook from REDMINE: issues | ' + 'action: ' + str(issue['action']) + '\n' +
              action_gh + ' result in GITHUB: ' + str(result.status_code) + ' ' + str(result.reason) + '\n' +
              'GITHUB  | ---------------- issue ----------------' + '\n' +
              '        | url:           ' + url_gh + '\n' +
              '        | issue_id:      ' + str(linked_issues.issue_id_gh) + '\n' +
              '        | repos_id:      ' + str(repos_id_gh) + '\n' +
              '        | issue_number:  ' + str(linked_issues.issue_num_gh) + '\n' +
              '        |\n' +
              'REDMINE | ---------------- issue ----------------' + '\n' +
              '        | author_id:     ' + str(issue['issue_author_id']) + '\n' +
              '        | author_login:  ' + str(issue['issue_author_login']) + '\n' +
              '        | issue_url:     ' + issue['issue_url'] + '\n' +
              '        | issue_id:      ' + str(issue['issue_id']) + '\n' +
              '        | project_id:    ' + str(issue['project_id']))

# при изменении в редмайне: всегда оставляем комментарий об изменении в гитхабе, затем производим сами изменения
def log_comment_rm(result, issue, linked_issues, linked_comments):

    action_gh = 'POST'
    repos_id_gh = linked_issues.repos_id_gh
    url_gh = make_gh_repos_url(repos_id_gh)

    WRITE_LOG(action_gh + ' result in GITHUB: ' + str(result.status_code) + ' ' + str(result.reason) + '\n' +
              'GITHUB  | ---------------- issue ----------------' + '\n' +
              '        | url_gh:        ' + url_gh + '\n' +
              '        | issue_id:      ' + str(linked_issues.issue_id_gh) + '\n' +
              '        | repos_id:      ' + str(repos_id_gh) + '\n' +
              '        | issue_number:  ' + str(linked_issues.issue_num_gh) + '\n' +
              '        | --------------- comment ---------------' + '\n' +
              '        | comment_id:    ' + str(linked_comments.comment_id_gh) + '\n' +
              '        |\n' +
              'REDMINE | ---------------- issue ----------------' + '\n' +
              '        | author_id:     ' + str(issue['issue_author_id']) + '\n' +
              '        | author_login:  ' + str(issue['issue_author_login']) + '\n' +
              '        | issue_url:     ' + issue['issue_url'] + '\n' +
              '        | issue_id:      ' + str(issue['issue_id']) + '\n' +
              '        | project_id:    ' + str(issue['project_id'])  + '\n' +
              '        | --------------- comment ---------------' + '\n' +
              '        | author_id:     ' + str(issue['comment_author_id']) + '\n' +
              '        | author_login:  ' + str(issue['comment_author_login']) + '\n' +
              '        | comment_id:    ' + str(issue['comment_id']))

def log_issue_edit_rm(result, issue, linked_issues):

    action_gh = 'EDIT'
    repos_id_gh = linked_issues.repos_id_gh
    url_gh = make_gh_repos_url(repos_id_gh)

    # изменили без комментария
    if (issue['comment_body'] == ''):
        WRITE_LOG(action_gh + ' result in GITHUB: ' + str(result.status_code) + ' ' + str(result.reason) + '\n' +
                  'GITHUB  | ---------------- issue ----------------' + '\n' +
                  '        | url_gh:        ' + url_gh + '\n' +
                  '        | issue_id:      ' + str(linked_issues.issue_id_gh) + '\n' +
                  '        | repos_id:      ' + str(repos_id_gh) + '\n' +
                  '        | issue_number:  ' + str(linked_issues.issue_num_gh) + '\n' +
                  '        |\n' +
                  'REDMINE | ---------------- issue ----------------' + '\n' +
                  '        | author_id:     ' + str(issue['issue_author_id']) + '\n' +
                  '        | author_login:  ' + str(issue['issue_author_login']) + '\n' +
                  '        | issue_url:     ' + issue['issue_url'] + '\n' +
                  '        | issue_id:      ' + str(issue['issue_id']) + '\n' +
                  '        | project_id:    ' + str(issue['project_id']))

    # изменили с комментарием
    else:
        WRITE_LOG(action_gh + ' result in GITHUB: ' + str(result.status_code) + ' ' + str(result.reason) + '\n' +
                  'GITHUB  | ---------------- issue ----------------' + '\n' +
                  '        | url_gh:        ' + url_gh + '\n' +
                  '        | issue_id:      ' + str(linked_issues.issue_id_gh) + '\n' +
                  '        | repos_id:      ' + str(repos_id_gh) + '\n' +
                  '        | issue_number:  ' + str(linked_issues.issue_num_gh) + '\n' +
                  '        |\n' +
                  'REDMINE | ---------------- issue ----------------' + '\n' +
                  '        | author_id:     ' + str(issue['issue_author_id']) + '\n' +
                  '        | author_login:  ' + str(issue['issue_author_login']) + '\n' +
                  '        | issue_url:     ' + issue['issue_url'] + '\n' +
                  '        | issue_id:      ' + str(issue['issue_id']) + '\n' +
                  '        | project_id:    ' + str(issue['project_id'])  + '\n' +
                  '        | --------------- comment ---------------' + '\n' +
                  '        | author_id:     ' + str(issue['comment_author_id']) + '\n' +
                  '        | author_login:  ' + str(issue['comment_author_login']) + '\n' +
                  '        | comment_id:    ' + str(issue['comment_id']))
    return 0


def prevent_cyclic_issue_rm(issue):

    error_text = 'The user, who opened the issue: ' + issue['issue_author_login'] +\
                 ' | user id: ' + str(issue['issue_author_id']) + ' (our bot)\n' +\
                 'Aborting action, in order to prevent cyclic: GH -> S -> RM -> S -> GH -> ...'

    if (not allow_log_cyclic):
        return error_text

    WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
              'received webhook from REDMINE: issues | ' + 'action: ' + str(issue['action']) + '\n' +
              error_text)

def prevent_cyclic_comment_rm(issue):

    error_text = 'The user, who edited/commented the issue: ' + issue['comment_author_login'] +\
                 ' | user id: ' + str(issue['comment_author_id']) + ' (our bot)\n' +\
                 'Aborting action, in order to prevent cyclic: GH -> S -> RM -> S -> GH -> ...'

    if (not allow_log_cyclic):
        return error_text

    WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
              'received webhook from REDMINE: issues | ' + 'action: ' + str(issue['action']) + '\n' +
              error_text)

    return error_text

def log_link_comment_crutch(issue, linked_comments):

    response_text = 'The user, who edited/commented the issue: ' + issue['comment_author_login'] +\
                    ' | user id: ' + str(issue['comment_author_id']) + ' (our bot)\n' +\
                    'Comment linked to GITHUB successfully.'
    if (linked_comments == None):
        response_text += 'ERROR: Comment link to GITHUB was unsuccessfull'

    else:
        response_text += 'Comment linked to GITHUB successfully'

    if (not allow_log_cyclic):
        return response_text

    WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
              'received webhook from REDMINE: issues | ' + 'action: ' + str(issue['action']) + '\n' +
              response_text)

    return response_text


# ======================================================== GITHUB ======================================================


# ----------------------------------------------------- ФУНКЦИИ --------------------------------------------------

def make_gh_repos_url(repos_id_gh):

    url_gh = "https://api.github.com/repositories/" + str(repos_id_gh) + "/issues"

    return url_gh

def chk_if_gh_user_is_our_bot(user_id_gh):

    if (user_id_gh == BOT_ID_GH):
        return True

    else:
        return False


# при изменении в гитхабе: всегда оставляем комментарий об изменении в редмайне, затем производим сами изменения
def log_issue_gh(result, issue, linked_issues, project_id_rm):

    if (issue['action'] == 'opened'):
        action_rm = 'POST'

    elif (issue['action'] == 'deleted'):
        action_rm = 'DELETE'

    elif (issue['action'] == 'edited'):
        action_rm = 'EDIT'

    elif (issue['action'] == 'closed'):
        action_rm = 'EDIT'

    elif (issue['action'] == 'reopened'):
        action_rm = 'EDIT'

    elif (issue['action'] == 'labeled'):
        action_rm = 'EDIT'

    elif (issue['action'] == 'unlabeled'):
        action_rm = 'EDIT'

    else:
        action_rm = issue['action'] + ' (ERROR: invalid action)'

    WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
              'received webhook from GITHUB: issues | ' + 'action: ' + issue['action'] + '\n' +
              action_rm + ' result in REDMINE: ' + str(result.status_code) + ' ' + str(result.reason) + '\n' +
              'GITHUB  | sender_id:     ' + str(issue['sender_id']) + '\n' +
              '        | sender_login:  ' + str(issue['sender_login']) + '\n' +
              '        | ---------------- issue ----------------' + '\n' +
              '        | author_id:     ' + str(issue['issue_author_id']) + '\n' +
              '        | author_login:  ' + str(issue['issue_author_login']) + '\n' +
              '        | issue_url:     ' + issue['issue_url'] + '\n' +
              '        | issue_title:   ' + issue['issue_title'] + '\n' +
              '        | issue_id:      ' + str(issue['issue_id']) + '\n' +
              '        | repos_id:      ' + str(issue['repos_id']) + '\n' +
              '        | issue_number:  ' + str(issue['issue_number']) + '\n' +
              '        |\n' +
              'REDMINE | ---------------- issue ----------------' + '\n' +
              '        | url_rm:        ' + url_rm + '\n' +
              '        | issue_id:      ' + str(linked_issues.issue_id_rm) + '\n' +
              '        | project_id:    ' + str(project_id_rm))

def log_comment_gh(result, issue, linked_issues, project_id_rm):
#def log_comment_gh(result, issue, linked_issues, linked_comments):

    action_rm = 'EDIT'

    WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
              'received webhook from GITHUB: issues_comment | ' + 'action: ' + issue['action'] + '\n' +
              action_rm + ' result in REDMINE: ' + str(result.status_code) + ' ' + str(result.reason) + '\n' +
              'GITHUB  | sender_id:     ' + str(issue['sender_id']) + '\n' +
              '        | sender_login:  ' + str(issue['sender_login']) + '\n' +
              '        | ---------------- issue ----------------' + '\n' +
              '        | author_id:     ' + str(issue['issue_author_id']) + '\n' +
              '        | author_login:  ' + str(issue['issue_author_login']) + '\n' +
              '        | issue_url:     ' + issue['issue_url'] + '\n' +
              '        | issue_title:   ' + issue['issue_title'] + '\n' +
              '        | issue_id:      ' + str(issue['issue_id']) + '\n' +
              '        | repos_id:      ' + str(issue['repos_id']) + '\n' +
              '        | issue_number:  ' + str(issue['issue_number']) + '\n' +
              '        | --------------- comment ---------------' + '\n' +
              '        | author_id:     ' + str(issue['comment_author_id']) + '\n' +
              '        | author_login:  ' + str(issue['comment_author_login']) + '\n' +
              '        | comment_id:    ' + str(issue['comment_id']) + '\n' +
              '        |\n' +
              'REDMINE | ---------------- issue ----------------' + '\n' +
              '        | url_rm:        ' + url_rm + '\n' +
              '        | issue_id:      ' + str(linked_issues.issue_id_rm) + '\n' +
              '        | project_id:    ' + str(project_id_rm) + '\n')


def prevent_cyclic_issue_gh(issue):

    error_text = 'The user, who ' + issue['action'] + ' the issue: ' + issue['sender_login'] + \
                 ' | user id: ' + str(issue['sender_id']) + ' (our bot)\n' + \
                 'Aborting action, in order to prevent cyclic: GH -> S -> RM -> S -> GH -> ...'

    if (not allow_log_cyclic):
        return error_text

    WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
              'received webhook from GITHUB: issues | ' + 'action: ' + str(issue['action']) + '\n' +
              error_text)

    return error_text

def prevent_cyclic_comment_gh(issue):

    error_text = 'The user, who ' + issue['action'] + ' the comment: ' + issue['sender_login'] + \
                 ' | user id: ' + str(issue['sender_id']) + ' (our bot)\n' + \
                 'Aborting action, in order to prevent cyclic: GH -> S -> RM -> S -> GH -> ...'

    if (not allow_log_cyclic):
        return error_text

    WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
              'received webhook from GITHUB: issue_comment | ' + 'action: ' + str(issue['action']) + '\n' +
              error_text)

    return error_text
