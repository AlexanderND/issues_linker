import os
import datetime


# ===================================================== СПЕЦ. ФУНКЦИИ ==================================================


def WRITE_LOG(str):
    # получение абсолютного пути до файла
    script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
    log_file_name = os.path.join(script_dir, 'logs/server_log.txt')
    log = open(log_file_name, 'a')

    print(str)
    log.write(str + '\n')

    log.close()


# обработка спец. символов (\ -> \\)
def align_special_symbols(str):

    str = str.replace(r'"', r'\"')  # r - строка без спец. символов
    str = str.replace('\r', '\\r')
    str = str.replace('\n', '\\n')
    str = str.replace('\t', '\\t')

    return str


def read_file(file_path):
    # получение абсолютного пути до файла
    script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in

    file_path_absolute = os.path.join(script_dir, file_path)
    file_contents = open(file_path_absolute, 'r').read()    # загрузка данных из файла в строку

    return file_contents


# ======================================================== REDMINE =====================================================


# ------------------------------------------- КОНСТАНТЫ (локальный сервер) -----------------------------------------

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

# -------------------------------------------- КОНСТАНТЫ (реальный сервер) -----------------------------------------
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

# ----------------------------------------------------- ФУНКЦИИ -----------------------------------------------------

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
              'REDMINE | url:           ' + issue['issue_url'] + '\n' +
              '        | issue_title:   ' + issue['title'] + '\n' +
              '        | issue_id:      ' + str(issue['issue_id']) + '\n' +
              '        | project_id:    ' + str(issue['project_id']) + '\n' +
              '        | user_id:       ' + str(issue['user_id']) + '\n' +
              '        | user_login:    ' + str(issue['user_login']))
    return 0

# TODO: комментарий, вместо issue
# при изменении в редмайне: всегда оставляем комментарий об изменении в гитхабе, затем производим сами изменения
def link_log_rm_comment(result, issue, linked_issues, linked_comments):

    action_gh = 'POST'

    # изменили без комментария
    if (issue['comment_body'] == ''):
        WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
                  'received webhook from REDMINE: issues (edit) | ' + 'action: ' + str(issue['action']) + '\n' +
                  action_gh + ' result in GITHUB: ' + str(result.status_code) + ' ' + str(result.reason) + '\n' +
                  'GITHUB  | url:           ' + url_gh + '\n' +
                  '        | issue_id:      ' + str(linked_issues.issue_id_gh) + '\n' +
                  '        | repos_id:      ' + repos_id_gh + '\n' +
                  '        | issue_number:  ' + str(linked_issues.issue_num_gh) + '\n' +
                  'REDMINE | url:           ' + issue['issue_url'] + '\n' +
                  '        | issue_title:   ' + issue['title'] + '\n' +
                  '        | issue_id:      ' + str(issue['issue_id']) + '\n' +
                  '        | project_id:    ' + str(issue['project_id']) + '\n' +
                  '        | user_id:       ' + str(issue['user_id']) + '\n' +
                  '        | user_login:    ' + str(issue['user_login']))
    # изменили с комментарием
    else:
        WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
                  'received webhook from REDMINE: issues (edit with comment) | ' + 'action: ' + str(issue['action']) + '\n' +
                  action_gh + ' result in GITHUB: ' + str(result.status_code) + ' ' + str(result.reason) + '\n' +
                  'GITHUB  | url:           ' + url_gh + '\n' +
                  '        | issue_id:      ' + str(linked_issues.issue_id_gh) + '\n' +
                  '        | repos_id:      ' + repos_id_gh + '\n' +
                  '        | issue_number:  ' + str(linked_issues.issue_num_gh) + '\n' +
                  'REDMINE | url:           ' + issue['issue_url'] + '\n' +
                  '        | issue_title:   ' + issue['title'] + '\n' +
                  '        | issue_id:      ' + str(issue['issue_id']) + '\n' +
                  '        | project_id:    ' + str(issue['project_id']) + '\n' +
                  '        | user_id:       ' + str(issue['user_id']) + '\n' +
                  '        | user_login:    ' + str(issue['user_login']))
    return 0

def link_log_rm_edit(result, issue, linked_issues):

    action_gh = 'EDIT'

    # изменили без комментария
    if (issue['comment_body'] == ''):
        WRITE_LOG(action_gh + ' result in GITHUB: ' + str(result.status_code) + ' ' + str(result.reason) + '\n' +
                  'GITHUB  | url:           ' + url_gh + '\n' +
                  '        | issue_id:      ' + str(linked_issues.issue_id_gh) + '\n' +
                  '        | repos_id:      ' + repos_id_gh + '\n' +
                  '        | issue_number:  ' + str(linked_issues.issue_num_gh) + '\n' +
                  'REDMINE | url:           ' + issue['issue_url'] + '\n' +
                  '        | issue_title:   ' + issue['title'] + '\n' +
                  '        | issue_id:      ' + str(issue['issue_id']) + '\n' +
                  '        | project_id:    ' + str(issue['project_id']) + '\n' +
                  '        | user_id:       ' + str(issue['user_id']) + '\n' +
                  '        | user_login:    ' + str(issue['user_login']))
    # изменили с комментарием
    else:
        WRITE_LOG(action_gh + ' result in GITHUB: ' + str(result.status_code) + ' ' + str(result.reason) + '\n' +
                  'GITHUB  | url:           ' + url_gh + '\n' +
                  '        | issue_id:      ' + str(linked_issues.issue_id_gh) + '\n' +
                  '        | repos_id:      ' + repos_id_gh + '\n' +
                  '        | issue_number:  ' + str(linked_issues.issue_num_gh) + '\n' +
                  'REDMINE | url:           ' + issue['issue_url'] + '\n' +
                  '        | issue_title:   ' + issue['title'] + '\n' +
                  '        | issue_id:      ' + str(issue['issue_id']) + '\n' +
                  '        | project_id:    ' + str(issue['project_id']) + '\n' +
                  '        | user_id:       ' + str(issue['user_id']) + '\n' +
                  '        | user_login:    ' + str(issue['user_login']))
    return 0


def prevent_cyclic_rm(issue):
    if(issue['action'] == 'opened'):
        action_rm = 'opened'
    else:
        action_rm = 'edited'

    error_text = 'The user, who ' + action_rm + ' the issue: ' + issue['user_login'] +\
                 ' | user id: ' + str(issue['user_id']) + ' (our bot)\n' +\
                 'Aborting action, in order to prevent cyclic post: GH -> S -> RM -> S -> GH -> ...'

    WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
              'received webhook from REDMINE: issues | ' + 'action: ' + str(issue['action']) + '\n' +
              error_text)

    return error_text


# ======================================================== GITHUB ======================================================


# ---------------------------------------------------- КОНСТАНТЫ ---------------------------------------------------

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

# ----------------------------------------------------- ФУНКЦИИ -----------------------------------------------------

def chk_if_gh_user_is_a_bot(user_id_gh):
    if (user_id_gh == BOT_ID_GH):
        return True
    return False


def link_log_issue_gh(result, issue, linked_issues):

    if (issue['action'] == 'opened'):
        action_rm = 'POST'
    elif (issue['action'] == 'deleted'):
        action_rm = 'DELETE'
    elif (issue['action'] == 'edited'):
        action_rm = 'EDIT'
    else:
        action_rm = issue['action'] + ' (ERROR: invalid action)'

    WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
              'received webhook from GITHUB: issues | ' + 'action: ' + issue['action'] + '\n' +
              action_rm + ' result in REDMINE: ' + str(result.status_code) + ' ' + str(result.reason) + '\n' +
              'GITHUB  | url:           ' + issue['issue_url'] + '\n' +
              '        | issue_title:   ' + issue['title'] + '\n' +
              '        | issue_id:      ' + str(issue['issue_id']) + '\n' +
              '        | repos_id:      ' + str(issue['repos_id']) + '\n' +
              '        | issue_number:  ' + str(issue['issue_number']) + '\n' +
              '        | user_id:       ' + str(issue['user_id']) + '\n' +
              '        | user_login:    ' + str(issue['user_login']) + '\n' +
              'REDMINE | url:           ' + url_rm + '\n' +
              '        | issue_id:      ' + str(linked_issues.issue_id_rm) + '\n'
              '        | project_id:    ' + str(project_id_rm))
    return 0

# TODO: комментарий, вместо issue
def link_log_comment_gh(result, issue, linked_issues, linked_comments):

    action_rm = 'EDIT'

    WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
              'received webhook from GITHUB: issues_comment | ' + 'action: ' + issue['action'] + '\n' +
              action_rm + ' result in REDMINE: ' + str(result.status_code) + ' ' + str(result.reason) + '\n' +
              '---------ISSUES---------\n' +
              'GITHUB  | url:           ' + issue['issue_url'] + '\n' +
              '        | issue_title:   ' + issue['title'] + '\n' +
              '        | issue_id:      ' + str(issue['issue_id']) + '\n' +
              '        | repos_id:      ' + str(issue['repos_id']) + '\n' +
              '        | issue_number:  ' + str(issue['issue_number']) + '\n' +
              '        | user_id:       ' + str(issue['user_id']) + '\n' +
              '        | user_login:    ' + str(issue['user_login']) + '\n' +
              'REDMINE | url:           ' + url_rm + '\n' +
              '        | issue_id:      ' + str(linked_issues.issue_id_rm) + '\n'
              '        | project_id:    ' + str(project_id_rm) + '\n'
              '---------COMMENTS---------\n' +
              'GITHUB  | comment_id:    ' + str(linked_comments.comment_id_rm) + '\n' +
              'REDMINE | comment_id:    ' + str(linked_comments.comment_id_gh))
    return 0


def prevent_cyclic_gh(issue):

    error_text = 'The user, who ' + issue['action'] + ' the issue: ' + issue['user_login'] + \
                 ' | user id: ' + str(issue['user_id']) + ' (our bot)\n' + \
                 'Aborting action, in order to prevent cyclic deletion: GH -> S -> RM -> S -> GH -> ...'

    WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
              'received webhook from GITHUB: issues | ' + 'action: ' + str(issue['action']) + '\n' +
              error_text)

    return error_text

def prevent_cyclic_comment_gh(issue):

    error_text = 'The user, who ' + issue['action'] + ' the comment: ' + issue['user_login'] + \
                 ' | user id: ' + str(issue['user_id']) + ' (our bot)\n' + \
                 'Aborting action, in order to prevent cyclic deletion: GH -> S -> RM -> S -> GH -> ...'

    WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
              'received webhook from GITHUB: issue_comment | ' + 'action: ' + str(issue['action']) + '\n' +
              error_text)

    return error_text
