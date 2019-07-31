import requests
import datetime
from jinja2 import Template
import json
from django.http import HttpResponse                                # ответы серверу (гитхабу)

from issues_linker.quickstart.models import Linked_Projects         # связанные проекты
from issues_linker.quickstart.models import Linked_Issues           # связанные issues

from issues_linker.my_functions import WRITE_LOG                    # ведение логов
from issues_linker.my_functions import WRITE_LOG_GRN                # ведение логов (многократные действия)
from issues_linker.my_functions import align_special_symbols        # обработка спец. символов (\ -> \\)
from issues_linker.my_functions import read_file                    # загрузка файла (возвращает строку)

from issues_linker.my_functions import tracker_ids_rm               # ids трекеров задачи в редмайне
from issues_linker.my_functions import status_ids_rm                # ids статусов задачи в редмайне
from issues_linker.my_functions import priority_ids_rm              # ids приоритетов задачи в редмайне
from issues_linker.my_functions import url_rm                       # ссылка на сервер редмайна

from issues_linker.my_functions import chk_if_gh_user_is_our_bot    # проверка на бота (предотвращение
                                                                    # зацикливания: GH -> S -> RM -> ...)
from issues_linker.my_functions import prevent_cyclic_issue_gh      # предотвращение зацикливания

from issues_linker.my_functions import match_label_to_rm            # сопостовление label-а в гитхабе редмайну

from issues_linker.my_functions import del_bot_phrase               # удаление фразы бота

from issues_linker.my_functions import allign_request_result        # создание корректного ответа серверу

from issues_linker.my_functions import match_tracker_to_gh          # сопоставление label-ов
from issues_linker.my_functions import match_status_to_gh           # сопоставление label-ов
from issues_linker.my_functions import match_priority_to_gh         # сопоставление label-ов

from issues_linker.my_functions import make_gh_repos_url            # ссылка на гитхаб


def query_data_gh_to_rm(linked_projects):


    # =================================================== ПОДГОТОВКА ===================================================


    # авторизация в redmine по токену
    api_key_redmime = read_file('api_keys/api_key_redmime_local.txt')   # загрузка ключа для redmine api
    #api_key_redmime = read_file('api_keys/api_key_redmime.txt')        # загрузка ключа для redmine api
    api_key_redmime = api_key_redmime.replace('\n', '')                 # избавляемся от \n в конце строки

    # загрузка template из файла
    issue_redmine_template = read_file('data/issue_redmine_template.json')
    issue_redmine_template = Template(issue_redmine_template)           # шаблон для каждого issue в редмайне

    # заголовки авторизации и приложения, при отправке запросов на редмайн
    headers_rm = {'X-Redmine-API-Key': api_key_redmime,
                  'Content-Type': 'application/json'}


    # загрузка issue template из файла
    issue_github_template = read_file('data/issue_github_template.json')
    issue_github_template = Template(issue_github_template)  # шаблон для каждого issue

    # авторизация в гитхабе по токену
    api_key_github = read_file('api_keys/api_key_github.txt')           # загрузка ключа для github api
    api_key_github = api_key_github.replace('\n', '')                   # избавляемся от \n в конце строки

    # заголовки авторизации и приложения, при отправке запросов на гитхаб
    headers_gh = {'Authorization': 'token ' + api_key_github,
                  'Content-Type': 'application/json'}


    # ============================================ ВСПОМОГАТЕЛЬНЫЕ КОМАНДЫ =============================================


    # issue_body
    # comment_body_action
    # добавляем фразу бота, со ссылкой на аккаунт пользователя в гитхабе
    def add_bot_phrase(issue, to):

        # добавляем фразу бота к описанию issue
        if (to == 'issue_body'):

            # добавляем фразу бота
            author_url_gh = '"' + issue['issue_author_login'] + '":' + 'https://github.com/' + issue['issue_author_login']
            issue_url_gh = '"issue":' + issue['issue_url']
            issue_body = 'I am a bot, bleep-bloop.\n' +\
                         author_url_gh + ' Has opened the ' + issue_url_gh + ' in Github'
                         #author_url_gh + ' Has ' + issue['action'] + ' an issue on ' + issue_url_gh

            # добавляем описание задачи
            if (issue['issue_body'] == ''):
                issue_body += '.'

            else:
                # добавляем цитирование
                issue_body_ = issue['issue_body'].replace('\n', '\n>')
                issue_body_ = '>' + issue_body_

                issue_body += ': \n\n' + issue_body_

            return issue_body

        # добавляем фразу бота (комментарием) к действию в гитхабе (закрыл, изменил и т.д.)
        elif (to == 'comment_body_action'):

            author_url = '"' + issue['comment_author_login'] + '":' + 'https://github.com/' + issue['comment_author_login']
            issue_url = '"issue":' + issue['issue_url']
            comment_body = 'I am a bot, bleep-bloop.\n' +\
                         author_url + ' Has ' + issue['action'] + ' the ' + issue_url + ' in Github.'
                         #author_url + ' Has ' + issue['action'] + ' a comment on ' + issue_url + '.'

            return comment_body

        elif (to == 'comment_body_action'):

            author_url = '"' + issue['comment_author_login'] + '":' + 'https://github.com/' + issue['comment_author_login']
            issue_url = '"issue":' + issue['issue_url']
            comment_body = 'I am a bot, bleep-bloop.\n' +\
                         author_url + ' Has ' + issue['action'] + ' the ' + issue_url + ' in Github.'

            return comment_body

        else:

            WRITE_LOG("\nERROR: 'process_payload_from_gh.add_bot_phrase'\n" +
                      "unknown parameter 'to': " + to + '.\n' +
                      "Please, check your code on possible typos.\n" +
                      "Alternatively, add logic to process '" + to + "' parameter correctly.")

            return None

    # исправление label-ов в гитхабе
    def correct_gh_labels(issue, tracker, linked_issues):

        # добавление label-ов
        priority = match_priority_to_gh(linked_issues.priority_id_rm)
        status = match_status_to_gh(linked_issues.status_id_rm)


        # ---------------------------------------- ЗАГРУЗКА ДАННЫХ В ГИТХАБ ----------------------------------------


        issue_templated = issue_github_template.render(
            title=issue['issue_title'],
            body=issue['issue_body'],
            priority=priority,
            status=status,
            tracker=tracker)
        # кодировка Latin-1 на некоторых задачах приводит к ошибке кодировки в питоне
        issue_templated = issue_templated.encode('utf-8')

        url_gh = make_gh_repos_url(linked_issues.repos_id_gh)

        # добавление issue_id к ссылке
        issue_url_gh = url_gh + '/' + str(linked_issues.issue_num_gh)
        request_result = requests.patch(issue_url_gh,
                                   data=issue_templated,
                                   headers=headers_gh)

        return request_result


    # типичные ошибки на этапе проверки: не связаны проекты, задачи, комментарии, неизвестное действие и т.п.
    def PREPARATION_ERR(error_text, issue):

        # добавляем, чтобы в начале получилось: 'PREPARATION ERROR'
        error_text = 'PREPARATION ' + error_text

        WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
                  'received webhook from GITHUB: issues | ' + 'action: ' + str(issue['action']) + '\n' +
                  error_text)

        return HttpResponse(error_text, status=404)

    # логическая ошибка: неизвестное действие, неправильные label-ы в гитхабе и т.п.
    def LOGICAL_ERR(error_text, issue):

        # добавляем, чтобы в начале получилось: 'LOGICAL ERROR'
        error_text = 'LOGICAL ' + error_text

        WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
                  'received webhook from GITHUB: issues | ' + 'action: ' + str(issue['action']) + '\n' +
                  error_text)

        return HttpResponse(error_text, status=422)


    # обработка задачи
    def parse_issue_item(issue):

        issue_parsed = {}  # словарь issue (название, описание, ссылка)

        # заполение полей issue
        issue_parsed['issue_title'] = issue['title']
        issue_parsed['issue_body'] = issue['body']
        issue_parsed['issue_author_id'] = issue['user']['id']
        issue_parsed['issue_author_login'] = issue['user']['login']

        # идентификаторы (для связи и логов)
        issue_parsed['issue_id'] = issue['id']
        issue_parsed['repos_id'] = linked_projects.repos_id_gh
        issue_parsed['issue_number'] = issue['number']

        # ссылка на issue (для фразы бота и логов)
        issue_parsed['issue_url'] = issue['html_url']

        issue_parsed['labels'] = issue['labels']

        issue_parsed['action'] = 'opened'

        return issue_parsed

    # обработка комментария
    def parse_comment(comment):

        comment_parsed = {}  # словарь issue (название, описание, ссылка)

        # заполение полей issue
        comment_parsed['issue_title'] = comment['issue']['title']
        comment_parsed['issue_body'] = comment['issue']['body']
        comment_parsed['issue_author_id'] = comment['issue']['user']['id']  # автор issue
        comment_parsed['issue_author_login'] = comment['issue']['user']['login']

        # идентификаторы (для связи и логов)
        comment_parsed['issue_id'] = comment['issue']['id']
        comment_parsed['repos_id'] = comment['repository']['id']
        comment_parsed['issue_number'] = comment['issue']['number']

        # ссылка на issue (для фразы бота и логов)
        comment_parsed['issue_url'] = comment['issue']['html_url']

        # комментарий
        comment_parsed['comment_body'] = comment['comment']['body']
        comment_parsed['comment_id'] = comment['comment']['id']
        comment_parsed['comment_author_id'] = comment['comment']['user']['id']
        comment_parsed['comment_author_login'] = comment['comment']['user']['login']

        return comment_parsed


    def log_issue_gh(result, issue, linked_issues, project_id_rm):

        action_rm = 'POST'

        WRITE_LOG('\n  ' + '-' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '-' * 35 + '\n' +
                  '  linking issue from GITHUB to REDMINE\n' +
                  '  ' + action_rm + ' result in REDMINE: ' + str(result.status_code) + ' ' + str(result.reason) + '\n' +
                  '  GITHUB  | ---------------- issue ----------------' + '\n' +
                  '          | author_id:     ' + str(issue['issue_author_id']) + '\n' +
                  '          | author_login:  ' + str(issue['issue_author_login']) + '\n' +
                  '          | issue_url:     ' + issue['issue_url'] + '\n' +
                  '          | issue_title:   ' + issue['issue_title'] + '\n' +
                  '          | issue_id:      ' + str(issue['issue_id']) + '\n' +
                  '          | repos_id:      ' + str(issue['repos_id']) + '\n' +
                  '          | issue_number:  ' + str(issue['issue_number']) + '\n' +
                  '          |\n' +
                  '  REDMINE | ---------------- issue ----------------' + '\n' +
                  '          | url_rm:        ' + url_rm + '\n' +
                  '          | issue_id:      ' + str(linked_issues.issue_id_rm) + '\n' +
                  '          | project_id:    ' + str(
            project_id_rm))

    def log_comment_gh(result, issue, linked_issues, project_id_rm):

        action_rm = 'EDIT'

        WRITE_LOG('\n    ' + '-' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '-' * 35 + '\n' +
                  '    linking comment from GITHUB to REDMINE\n' +
                  '    ' + action_rm + ' result in REDMINE: ' + str(result.status_code) + ' ' + str(result.reason) + '\n' +
                  '    GITHUB  | ---------------- issue ----------------' + '\n' +
                  '            | author_id:     ' + str(issue['issue_author_id']) + '\n' +
                  '            | author_login:  ' + str(issue['issue_author_login']) + '\n' +
                  '            | issue_url:     ' + issue['issue_url'] + '\n' +
                  '            | issue_title:   ' + issue['issue_title'] + '\n' +
                  '            | issue_id:      ' + str(issue['issue_id']) + '\n' +
                  '            | repos_id:      ' + str(issue['repos_id']) + '\n' +
                  '            | issue_number:  ' + str(issue['issue_number']) + '\n' +
                  '            | --------------- comment ---------------' + '\n' +
                  '            | author_id:     ' + str(issue['comment_author_id']) + '\n' +
                  '            | author_login:  ' + str(issue['comment_author_login']) + '\n' +
                  '            | comment_id:    ' + str(issue['comment_id']) + '\n' +
                  '            |\n' +
                  '    REDMINE | ---------------- issue ----------------' + '\n' +
                  '            | url_rm:        ' + url_rm + '\n' +
                  '            | issue_id:      ' + str(linked_issues.issue_id_rm) + '\n' +
                  '            | project_id:    ' + str(project_id_rm) + '\n')


    # ============================================= КОМАНДЫ ДЛЯ ЗАГРУЗКИ ===============================================


    def post_issue(linked_projects, issue):


        # ----------------------------------------------- ПОДГОТОВКА ----------------------------------------------


        project_id_rm = linked_projects.project_id_rm

        # настройка label-ов
        tracker_id_rm = None
        status_id_rm = status_ids_rm[0]
        priority_id_rm = priority_ids_rm[0]

        for label in issue['labels']:

            tracker_rm = match_label_to_rm(label['name'])

            # если label известный
            if (tracker_rm != None):

                if (tracker_rm['type'] == 'Tracker'):

                    if (tracker_id_rm == None):
                        tracker_id_rm = tracker_rm['id_rm']

                    # если пользователь выбрал более одного трекера -> значение по умолчанию
                    else:
                        tracker_id_rm = tracker_ids_rm[0]

        # проверяем, был ли установлен трекер
        if (tracker_id_rm == None):
            tracker_id_rm = tracker_ids_rm[0]


        # ------------------------------------------ ОБРАБОТКА ФРАЗЫ БОТА -----------------------------------------


        #title = '[From Github] ' + issue['issue_title']
        title = issue['issue_title']
        issue_body = add_bot_phrase(issue, 'issue_body')   # добавляем фразу бота

        # обработка спец. символов
        title = align_special_symbols(title)
        issue_body = align_special_symbols(issue_body)


        # --------------------------------------- ЗАГРУЗКА ДАННЫХ В РЕДМАЙН ----------------------------------------


        issue_templated = issue_redmine_template.render(
            project_id=project_id_rm,
            tracker_id=tracker_id_rm,
            status_id=status_id_rm,
            priority_id=priority_id_rm,
            subject=title,
            description=issue_body)

        # кодировка по умолчанию (Latin-1) на некоторых задачах приводит к ошибке кодировки в питоне
        issue_templated = issue_templated.encode('utf-8')

        request_result = requests.post(url_rm,
                                       data=issue_templated,
                                       headers=headers_rm)


        # ------------------------------------------ СОХРАНЕНИЕ ДАННЫХ --------------------------------------------


        posted_issue = json.loads(request_result.text)

        # занесение в базу данных информацию о том, что данные issues связаны
        linked_issues = Linked_Issues.objects.create_linked_issues(
            posted_issue['issue']['id'],    # id issue в редмайне
            issue['issue_id'],              # id issue в гитхабе
            issue['repos_id'],              # id репозитория в гитхабе
            issue['issue_number'],          # номер issue  в репозитории гитхаба
            tracker_id_rm,                  # id трекера в редмайне
            status_id_rm,                   # id статуса в редмайне
            priority_id_rm)                 # id приоритета в редмайне

        # добавляем linked_issues в linked_projects
        linked_projects.add_linked_issues(linked_issues)

        # корректируем label-ы в гитхабе
        tracker = match_tracker_to_gh(linked_issues.tracker_id_rm)
        correct_gh_labels(issue, tracker, linked_issues)


        # ДЕБАГГИНГ
        log_issue_gh(request_result, issue, linked_issues, linked_projects.project_id_rm)

        result = {}
        result['request_result'] = request_result
        result['linked_issues'] = request_result

        return request_result

    def post_comment(linked_projects, issue):


        # ----------------------------------------------- ПОДГОТОВКА ----------------------------------------------


        project_id_rm = linked_projects.project_id_rm

        linked_issues = linked_projects.get_issue_by_id_gh(issue['issue_id'])

        # дополнительная проверка, что issue связаны
        if (linked_issues.count() == 0):

            error_text = "ERROR: process_comment_payload_from_gh.post_comment\n" +\
                         "comment " + str(issue['action']) + " in GITHUB, but the issue is not linked to REDMINE"

            return PREPARATION_ERR(error_text, issue)

        linked_issues = linked_issues[0]


        # ------------------------------------------ ОБРАБОТКА ФРАЗЫ БОТА -----------------------------------------


        # проверяем, если автор issue - бот
        if (chk_if_gh_user_is_our_bot(issue['issue_author_id'])):
            issue_body = del_bot_phrase(issue['issue_body'])

        else:
            issue_body = add_bot_phrase(issue, 'issue_body')

        comment_body = add_bot_phrase(issue, 'comment_body')    # добавляем фразу бота

        # обработка спец. символов
        issue_title = align_special_symbols(issue['issue_title'])
        issue_body = align_special_symbols(issue_body)
        comment_body = align_special_symbols(comment_body)


        # --------------------------------------- ЗАГРУЗКА ДАННЫХ В РЕДМАЙН ----------------------------------------


        issue_templated = issue_redmine_template.render(
            project_id=project_id_rm,
            issue_id=linked_issues.issue_id_rm,
            priority_id=linked_issues.priority_id_rm,
            subject=issue_title,
            description=issue_body,
            notes=comment_body)

        # кодировка Latin-1 на некоторых задачах приводит к ошибке кодировки в питоне
        issue_templated = issue_templated.encode('utf-8')

        issue_url_rm = url_rm.replace('.json',
                                      '/' + str(linked_issues.issue_id_rm) + '.json')
        request_result = requests.put(issue_url_rm,
                                      data=issue_templated,
                                      headers=headers_gh)


        # ------------------------------------------ СОХРАНЕНИЕ ДАННЫХ --------------------------------------------
        # (делаем привязку комментариев после получения веб-хука от редмайна)


        # ДЕБАГГИНГ
        log_comment_gh(request_result, issue, linked_issues, linked_projects.project_id_rm)

        return request_result


    # добавляем пробелы, чтобы отделить от лога проектов и задач (как табуляция)
    def log_link_comments_start():

        WRITE_LOG_GRN('\n    ' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
                      "    LINKING CJMMENTS BETWEEN ISSUES" + '\n' +
                      '    GITHUB       | ---------------------------------------' + '\n' +
                      '                 | repos_id:     ' + str(linked_projects.repos_id_gh) + '\n' +
                      '                 | repos_url:    ' + linked_projects.url_gh + '\n' +
                      '    REDMINE      | ---------------------------------------' + '\n' +
                      '                 | project_id:   ' + str(linked_projects.project_id_rm) + '\n' +
                      '                 | project_url:  ' + linked_projects.url_rm)

    def log_link_comments_finish():

        WRITE_LOG_GRN("    FINISHED LINKING COMMENTS BETWEEN ISSUES" + '\n' +
                      '    GITHUB       | ---------------------------------------' + '\n' +
                      '                 | repos_id:     ' + str(linked_projects.repos_id_gh) + '\n' +
                      '                 | repos_url:    ' + linked_projects.url_gh + '\n' +
                      '    REDMINE      | ---------------------------------------' + '\n' +
                      '                 | project_id:   ' + str(linked_projects.project_id_rm) + '\n' +
                      '                 | project_url:  ' + linked_projects.url_rm + '\n' +
                      '\n    ' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n')

    # добавляем пробелы, чтобы отделить от лога проектов (как табуляция)
    def log_link_issues_start():

        WRITE_LOG_GRN('\n  ' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
                      "  LINKING ISSUES BETWEEN PROJECTS" + '\n' +
                      '  GITHUB       | ---------------------------------------' + '\n' +
                      '               | repos_id:     ' + str(linked_projects.repos_id_gh) + '\n' +
                      '               | repos_url:    ' + linked_projects.url_gh + '\n' +
                      '  REDMINE      | ---------------------------------------' + '\n' +
                      '               | project_id:   ' + str(linked_projects.project_id_rm) + '\n' +
                      '               | project_url:  ' + linked_projects.url_rm)

    def log_link_issues_finish():

        WRITE_LOG_GRN("  FINISHED LINKING ISSUES BETWEEN PROJECTS" + '\n' +
                      '  GITHUB       | ---------------------------------------' + '\n' +
                      '               | repos_id:     ' + str(linked_projects.repos_id_gh) + '\n' +
                      '               | repos_url:    ' + linked_projects.url_gh + '\n' +
                      '  REDMINE      | ---------------------------------------' + '\n' +
                      '               | project_id:   ' + str(linked_projects.project_id_rm) + '\n' +
                      '               | project_url:  ' + linked_projects.url_rm + '\n' +
                      '\n  ' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n')


    def query_issues_log(logs_):

        logs = ''

        for log in logs_:

            logs+= log

        return logs


    # ====================================== ЗАГРУЗКА ДАННЫХ ИЗ GITHUB В REDMINE =======================================


    # загрузка комментариев у задачи
    def query_gh_comments(linked_issues):

        log_link_comments_start()



        log_link_comments_finish()

    # загрузка задач у проекта
    def query_gh_issues(linked_projects):


        # ----------------------------------------------- ПОДГОТОВКА ----------------------------------------------


        log_link_issues_start()

        repos_url_gh = linked_projects.url_gh[19:]     # избавляемся от 'https://github.com/'

        # запрос кол-ва всех issue
        url_gh = 'https://api.github.com/search/issues?q=repo:' + repos_url_gh
        request_result = requests.get(url_gh)   # для total_count

        num_issues = json.loads(request_result.text)['total_count']


        # ----------------------------------- ЗАПРОС ВСЕХ ЗАДАЧ С ПРОЕКТА В ГИТХАБЕ ------------------------------------


        issues = []
        WRITE_LOG('  QUERRYING ISSUES FROM GITHUB')

        per_page = 6  # для тестов
        #per_page = 100  # кол-во issue за страницу
        page = 1

        # цикл перехода по всем страницам, по 100 issue за страницу
        while True:

            WRITE_LOG('  page: ' + str(page) + ' | status: ' + str(request_result.status_code) + ' ' + str(request_result.reason))

            ''' https://api.github.com/search/issues?q=repo:AlexanderND/issues_linker_auto_labels_test/issues&per_page=5&page=1 '''
            url = url_gh + '/issues&per_page=' + str(per_page) + '&page=' + str(page)
            request_result = requests.get(url)

            issues_on_page = json.loads(request_result.text)['items']

            i = 1
            # цикл перебора всех задач на странице
            for issue in issues_on_page:

                issue_parsed = parse_issue_item(issue)

                # сохраняем данные
                issues.append(issue_parsed)

            # переход на след. страницу
            page += 1

            # цикл с постусловием
            if (page > 1 + num_issues / per_page):
                break



        # --------------------------------- ОТПРАВКА ЗАДАЧ В СВЯЗАННЫЙ ПРОЕКТ В РЕДМАЙНЕ -------------------------------


        # отправляем задачи в редмайн в обратном порядке
        for issue in reversed(issues):

            post_result = post_issue(linked_projects, issue)
            # TODO: запрашивать комменты к задаче


        log_link_issues_finish()


    query_gh_issues(linked_projects)

    '''# ------------------------------------------------------------------ЗАГРУЗКА ДАННЫХ В REDMINE-------------------------------------------------------------------
    WRITE_LOG('----------dumping issues----------')

    project_id = 455  # 455 - тестовый проект
    tracker_id = 3  # Задача
    status_id = 1  # Новое
    priority_id = 4  # Нормальный

    # выгрузка данных через шаблон
    from jinja2 import Template
    parsed_data_template = Template(issue_redmine_template)  # шаблон для каждого issue
    url_rm = "https://redmine.redsolution.ru/issues.json"

    # обработка спец. символов (\ -> \\)
    def allign(str):
        str = str.replace(r'"', r'\"')  # r - строка без спец. символов
        str = str.replace('\r', '\\r')
        str = str.replace('\n', '\\n')
        str = str.replace('\t', '\\t')
        return str

    def delete_issue(issue):
        url = repos_url + str(issue['id']) + '/'
        r = requests.delete(url)

        if (r.status_code == 204):
            return ' | ' + str(r.status_code) + ' ' + str(r.reason) + ' (deleted from server)'
        else:
            return ' | ' + str(r.status_code) + ' ' + str(r.reason) + ' (NOT deleted from server)'

    def push_issue(issue):
        subject = allign(issue['title'])
        description = allign(issue['title'])

        issue_templated = parsed_data_template.render(
            project_id=project_id,
            tracker_id=tracker_id,
            status_id=status_id,
            priority_id=priority_id,
            subject=subject,
            description=description)

        issue_templated = issue_templated.encode(
            'utf-8')  # кодировка Latin-1 на некоторых задачах приводит к ошибке кодировки в питоне

        r = requests.post(url_rm,
                          data=issue_templated,
                          headers={'X-Redmine-API-Key': api_key_redmime, 'Content-Type': 'application/json'})

        if (r.status_code == 201):
            delete_result = delete_issue(issue)
            return str(r.status_code) + ' ' + str(r.reason) + ' (pushed to rm)' + delete_result
        else:
            return str(r.status_code) + ' ' + str(r.reason) + ' (NOT pushed to rm) | (NOT deleted from server)'

    issue_index = 0
    for issue in issues_parsed:
        if (issue['action'] == 'opened'):
            push_result = push_issue(issue)
            WRITE_LOG(str(issue_index) + ': ' + push_result +
                      ' | action: ' + str(issue['action']))  # ДЕБАГГИНГ
        else:
            delete_result = delete_issue(issue)
            WRITE_LOG(str(issue_index) + ': ' + delete_result +
                      ' | action: ' + str(issue['action']) + ' (wrong action)')

        issue_index += 1

    WRITE_LOG('----------all done!---------------')'''
