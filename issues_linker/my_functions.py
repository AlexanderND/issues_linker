import os
import datetime

from django.http import HttpResponse    # ответы серверу


# ===================================================== СПЕЦ. ФУНКЦИИ ==================================================


def WRITE_LOG(string):

    string = str(string)

    # получение абсолютного пути до файла
    script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
    log_file_name = os.path.join(script_dir, 'logs/server_log.txt')
    log = open(log_file_name, 'a')

    print(string)
    log.write(string + '\n')

    log.close()


# обработка спец. символов (\ -> \\)
def align_special_symbols(str):

    str = str.replace(r'"', r'\"')  # r - строка без спец. символов
    str = str.replace('\r', '\\r')
    str = str.replace('\n', '\\n')
    str = str.replace('\t', '\\t')

    return str

# чтение файла
def read_file(file_path):
    # получение абсолютного пути до файла
    script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in

    file_path_absolute = os.path.join(script_dir, file_path)
    file_contents = open(file_path_absolute, 'r').read()    # загрузка данных из файла в строку

    return file_contents

# удаление фразы бота из текста
def del_bot_phrase(body):

    body_parts = body.split(': ')  # разбиваем body на части (часть 0 - фраза бота)
    WRITE_LOG(str(body_parts))

    # если body пустой - значит, фраза бота закончилась на точку (нет опсания)
    if (len(body_parts) == 1):
        body_processed = ''

    else:
        body_processed = body_parts[1] + ': '

        WRITE_LOG(len(body_parts))
        for body_part in range(2, len(body_parts) - 1):
            body_processed += body_parts[body_part] + ': '

        body_processed += body_parts[len(body_parts) - 1]
        body_processed = body_processed.replace('\n>', '\n')    # убираем цитирование бота (ВОЗМОЖНЫ ОШИБКИ)'''

    return body_processed

# создание корректного ответа серверу
def allign_request_result(request_result):

    if (type(request_result) is HttpResponse):

        return request_result

    else:

        request_result = HttpResponse(request_result.text, status=request_result.status_code)
        return request_result


# ======================================================== REDMINE =====================================================


# ------------------------------------------- КОНСТАНТЫ (локальный сервер) ---------------------------------------

BOT_ID_RM = 6           # id бота в редмайне (предотвращение зацикливания)

project_id_rm = 2       # 2 - проект на локальном сервере редмайна (тестовый сервер)

# 0 (4)  - Задача
# 1 (5)  - Ошибка
tracker_ids_rm = [4, 5]

# 0 (7)  - Новый
# 1 (8)  - Выполнение: в работе
# 2 (9)  - Выполнение: обратная связь
# 3 (10) - Выполнение: проверка
# 4 (11) - Отказ
# 5 (12) - Закрыт
status_ids_rm = [7, 8, 9, 10, 11, 12]

# 0 (11) - Нормальный
# 1 (10) - Низкий
# 2 (12) - Высокий
priority_ids_rm = [11, 10, 12]


url_rm = "http://localhost:3000/issues.json"    # локальный сервер редмайна (тестовый сервер)

# -------------------------------------------- КОНСТАНТЫ (реальный сервер) ---------------------------------------
'''
BOT_ID_RM = 6           # id бота в редмайне (предотвращение зацикливания)

project_id_rm = 455     # 455 - тестовый проект

# 0 (3) - Задача
# 1 (1) - Ошибка
tracker_ids_rm = [ 3, 1 ]

# 0 (1) - Новый
# 1 (2) - Выполнение: в работе
# 2 (4) - Выполнение: обратная связь
# 3 (7) - Выполнение: проверка
# 4 (6) - Отказ
# 5 (5) - Закрыт
status_ids_rm = [ 1, 2, 4, 7, 6, 5 ]

# 0 (4) - Нормальный
# 1 (3) - Низкий
# 2 (5) - Высокий
priority_ids_rm = [ 4, 3, 5 ]

url_rm = "https://redmine.redsolution.ru/issues.json"
'''

# ----------------------------------------------------- ФУНКЦИИ --------------------------------------------------

def chk_if_rm_user_is_a_bot(user_id_rm):
    if (user_id_rm == BOT_ID_RM):
        return True
    return False


def link_log_rm_post(result, issue, linked_issues):

    action_gh = 'POST'

    WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
              'received webhook from REDMINE: issues | ' + 'action: ' + str(issue['action']) + '\n' +
              action_gh + ' result in GITHUB: ' + str(result.status_code) + ' ' + str(result.reason) + '\n' +
              'GITHUB  | url:           ' + url_gh + '\n' +
              '        | issue_id:      ' + str(linked_issues.issue_id_gh) + '\n' +
              '        | repos_id:      ' + repos_id_gh + '\n' +
              '        | issue_number:  ' + str(linked_issues.issue_num_gh) + '\n' +
              'REDMINE | author_id:     ' + str(issue['issue_author_id']) + '\n' +
              '        | author_login:  ' + str(issue['issue_author_login']) + '\n' +
              '        | issue_url:     ' + issue['issue_url'] + '\n' +
              '        | issue_id:      ' + str(issue['issue_id']) + '\n' +
              '        | project_id:    ' + str(issue['project_id']))
    return 0

# при изменении в редмайне: всегда оставляем комментарий об изменении в гитхабе, затем производим сами изменения
def link_log_rm_comment(result, issue, linked_issues, linked_comments):

    action_gh = 'POST'

    WRITE_LOG(action_gh + ' result in GITHUB: ' + str(result.status_code) + ' ' + str(result.reason) + '\n' +
              'GITHUB  | ---------------- issue ----------------' + '\n' +
              '        | url_gh:        ' + url_gh + '\n' +
              '        | issue_id:      ' + str(linked_issues.issue_id_gh) + '\n' +
              '        | repos_id:      ' + repos_id_gh + '\n' +
              '        | issue_number:  ' + str(linked_issues.issue_num_gh) + '\n' +
              '        | --------------- comment ---------------' + '\n' +
              '        | comment_id:    ' + str(linked_comments.comment_id_gh) + '\n' +
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

def link_log_rm_edit(result, issue, linked_issues):

    action_gh = 'EDIT'

    if (result.status_code == 403):
        WRITE_LOG(action_gh + ' result in GITHUB: ' + str(result.status_code) + ' ' + str(result.reason))
    # изменили без комментария
    elif (issue['comment_body'] == ''):
        WRITE_LOG(action_gh + ' result in GITHUB: ' + str(result.status_code) + ' ' + str(result.reason) + '\n' +
                  'GITHUB  | url_gh:        ' + url_gh + '\n' +
                  '        | issue_id:      ' + str(linked_issues.issue_id_gh) + '\n' +
                  '        | repos_id:      ' + repos_id_gh + '\n' +
                  '        | issue_number:  ' + str(linked_issues.issue_num_gh) + '\n' +
                  'REDMINE | author_id:     ' + str(issue['issue_author_id']) + '\n' +
                  '        | author_login:  ' + str(issue['issue_author_login']) + '\n' +
                  '        | issue_url:     ' + issue['issue_url'] + '\n' +
                  '        | issue_id:      ' + str(issue['issue_id']) + '\n' +
                  '        | project_id:    ' + str(issue['project_id']))
    # изменили с комментарием
    else:
        WRITE_LOG(action_gh + ' result in GITHUB: ' + str(result.status_code) + ' ' + str(result.reason) + '\n' +
                  'GITHUB  | url_gh:        ' + url_gh + '\n' +
                  '        | issue_id:      ' + str(linked_issues.issue_id_gh) + '\n' +
                  '        | repos_id:      ' + repos_id_gh + '\n' +
                  '        | issue_number:  ' + str(linked_issues.issue_num_gh) + '\n' +
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
    if(issue['action'] == 'opened'):
        action_rm = 'opened'
    else:
        action_rm = 'edited'

    error_text = 'The user, who opened the issue: ' + issue['issue_author_login'] +\
                 ' | user id: ' + str(issue['issue_author_id']) + ' (our bot)\n' +\
                 'Aborting action, in order to prevent cyclic post: GH -> S -> RM -> S -> GH -> ...'

    WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
              'received webhook from REDMINE: issues | ' + 'action: ' + str(issue['action']) + '\n' +
              error_text)

def prevent_cyclic_comment_rm(issue):
    if(issue['action'] == 'opened'):
        action_rm = 'opened'
    else:
        action_rm = 'edited'

    error_text = 'The user, who edited/commented the issue: ' + issue['comment_author_login'] +\
                 ' | user id: ' + str(issue['comment_author_id']) + ' (our bot)\n' +\
                 'Aborting action, in order to prevent cyclic post: GH -> S -> RM -> S -> GH -> ...'

    WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
              'received webhook from REDMINE: issues | ' + 'action: ' + str(issue['action']) + '\n' +
              error_text)

    return error_text


# функция сопостовления label-а в гитхабе редмайну
def match_label_to_rm(label_gh):

    label = {}

    label['type'], label['name'] = str(label_gh).split(': ', 1)

    if (label['type'] == 'Приоритет'):
        if (label['name'] == 'низкий'):
            label['id_rm'] = priority_ids_rm[1]
        elif (label['name'] == 'нормальный'):
            label['id_rm'] = priority_ids_rm[0]
        elif (label['name'] == 'высокий'):
            label['id_rm'] = priority_ids_rm[2]
        else:
            WRITE_LOG('ERROR: UNKNOWN PRIORITY: ' + str(label_gh) +
                      ' (type: ' + str(label['type']) + 'name: ' + str(label['name']) + ')')
            label['id_rm'] = priority_ids_rm[0]
        
    elif (label['type'] == 'Статус'):
        if (label['name'] == 'новый'):
            label['id_rm'] = status_ids_rm[0]
        if (label['name'] == 'в работе'):
            label['id_rm'] = status_ids_rm[1]
        if (label['name'] == 'обратная связь'):
            label['id_rm'] = status_ids_rm[2]
        if (label['name'] == 'проверка'):
            label['id_rm'] = status_ids_rm[3]
        if (label['name'] == 'отказ'):
            label['id_rm'] = status_ids_rm[4]
        if (label['name'] == 'закрыт'):
            label['id_rm'] = status_ids_rm[5]
        else:
            WRITE_LOG('ERROR: UNKNOWN STATUS: ' + str(label_gh) +
                      ' (type: ' + str(label['type']) + 'name: ' + str(label['name']) + ')')
            label['id_rm'] = status_ids_rm[0]

    elif (label['type'] == 'Трекер'):
        if (label['name'] == 'задача'):
            label['id_rm'] = tracker_ids_rm[0]
        if (label['name'] == 'ошибка'):
            label['id_rm'] = tracker_ids_rm[1]
        else:
            WRITE_LOG('ERROR: UNKNOWN TRACKER: ' + str(label_gh) +
                      ' (type: ' + str(label['type']) + 'name: ' + str(label['name']) + ')')
            label['id_rm'] = tracker_ids_rm[0]

    else:
        WRITE_LOG('ERROR: UNKNOWN LABEL: ' + str(label_gh))
        label['id_rm'] = None

    return label

# функция сопостовления label-а в редмайне гитхабу
def match_label_to_gh(label_rm):

    label = {}

    label['type'], label['name'] = str(label_rm).split(': ')

    if (label['type'] == 'Приоритет'):
        if (label['name'] == 'низкий'):
            label['id_rm'] = priority_ids_rm[1]
        elif (label['name'] == 'нормальный'):
            label['id_rm'] = priority_ids_rm[0]
        elif (label['name'] == 'высокий'):
            label['id_rm'] = priority_ids_rm[2]
        else:
            WRITE_LOG('ERROR: UNKNOWN PRIORITY')
            label['id_rm'] = priority_ids_rm[0]

    elif (label['type'] == 'Статус'):
        if (label['name'] == 'новый'):
            label['id_rm'] = status_ids_rm[0]
        if (label['name'] == 'в работе'):
            label['id_rm'] = status_ids_rm[1]
        if (label['name'] == 'обратная связь'):
            label['id_rm'] = status_ids_rm[2]
        if (label['name'] == 'проверка'):
            label['id_rm'] = status_ids_rm[3]
        if (label['name'] == 'отказ'):
            label['id_rm'] = status_ids_rm[4]
        if (label['name'] == 'закрыт'):
            label['id_rm'] = status_ids_rm[5]
        else:
            WRITE_LOG('ERROR: UNKNOWN PRIORITY')
            label['id_rm'] = status_ids_rm[0]

    elif (label['type'] == 'Трекер'):
        if (label['name'] == 'задача'):
            label['id_rm'] = tracker_ids_rm[0]
        if (label['name'] == 'ошибка'):
            label['id_rm'] = tracker_ids_rm[1]
        else:
            WRITE_LOG('ERROR: UNKNOWN PRIORITY')
            label['id_rm'] = tracker_ids_rm[0]

    else:
        WRITE_LOG('ERROR: UNKNOWN LABEL')
        label['id_rm'] = None

    return label


# ======================================================== GITHUB ======================================================


# ---------------------------------------------------- КОНСТАНТЫ -------------------------------------------------

BOT_ID_GH = 53174303        # id бота в гитхабе (предотвращение зацикливания)

repos_id_gh = '194635238'   # id репозитория в гитхабе
url_gh = "https://api.github.com/repositories/" + repos_id_gh + "/issues"

# 4 - Задача
# 5 - Ошибка
tracker_id_gh = 4

# 7  - Новый
# 8  - Выполнение: в работе
# 9  - Выполнение: обратная связь
# 10 - Выполнение: проверка
# 11 - Отказ
# 12 - Закрыт
status_id_gh = 7

# 10 - Низкий
# 11 - Нормальный
# 12 - Высокий
priority_id_gh = 11

# ----------------------------------------------------- ФУНКЦИИ --------------------------------------------------

def chk_if_gh_user_is_a_bot(user_id_gh):
    if (user_id_gh == BOT_ID_GH):
        return True
    return False


# при изменении в гитхабе: всегда оставляем комментарий об изменении в редмайне, затем производим сами изменения
def link_log_issue_gh(result, issue, linked_issues):

    if (issue['action'] == 'opened'):
        action_rm = 'POST'
    elif (issue['action'] == 'deleted'):
        action_rm = 'DELETE'
    elif (issue['action'] == 'edited'):
        action_rm = 'EDIT'
    elif (issue['action'] == 'labeled'):
        action_rm = 'EDIT'
    else:
        action_rm = issue['action'] + ' (ERROR: invalid action)'

    WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
              'received webhook from GITHUB: issues | ' + 'action: ' + issue['action'] + '\n' +
              action_rm + ' result in REDMINE: ' + str(result.status_code) + ' ' + str(result.reason) + '\n' +
              'GITHUB  | sender_id:     ' + str(issue['sender_id']) + '\n' +
              '        | sender_login:  ' + str(issue['sender_login']) + '\n' +
              '        | ---------------- issue ----------------' + '\n' 
              '        | author_id:     ' + str(issue['issue_author_id']) + '\n' +
              '        | author_login:  ' + str(issue['issue_author_login']) + '\n' +
              '        | issue_url:     ' + issue['issue_url'] + '\n' +
              '        | issue_title:   ' + issue['issue_title'] + '\n' +
              '        | issue_id:      ' + str(issue['issue_id']) + '\n' +
              '        | repos_id:      ' + str(issue['repos_id']) + '\n' +
              '        | issue_number:  ' + str(issue['issue_number']) + '\n' +
              'REDMINE | url_rm:        ' + url_rm + '\n' +
              '        | issue_id:      ' + str(linked_issues.issue_id_rm) + '\n'
              '        | project_id:    ' + str(project_id_rm))
    return 0

def link_log_comment_gh(result, issue, linked_issues):
#def link_log_comment_gh(result, issue, linked_issues, linked_comments):

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
              'REDMINE | url_rm:        ' + url_rm + '\n' +
              '        | issue_id:      ' + str(linked_issues.issue_id_rm) + '\n'
              '        | project_id:    ' + str(project_id_rm) + '\n')

    return 0


def prevent_cyclic_issue_gh(issue):

    error_text = 'The user, who ' + issue['action'] + ' the issue: ' + issue['sender_login'] + \
                 ' | user id: ' + str(issue['sender_id']) + ' (our bot)\n' + \
                 'Aborting action, in order to prevent cyclic deletion: GH -> S -> RM -> S -> GH -> ...'

    WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
              'received webhook from GITHUB: issues | ' + 'action: ' + str(issue['action']) + '\n' +
              error_text)

    return error_text

def prevent_cyclic_comment_gh(issue):

    error_text = 'The user, who ' + issue['action'] + ' the comment: ' + issue['sender_login'] + \
                 ' | user id: ' + str(issue['sender_id']) + ' (our bot)\n' + \
                 'Aborting action, in order to prevent cyclic deletion: GH -> S -> RM -> S -> GH -> ...'

    WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
              'received webhook from GITHUB: issue_comment | ' + 'action: ' + str(issue['action']) + '\n' +
              error_text)

    return error_text
