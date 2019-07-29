import requests
import datetime
from jinja2 import Template
import json
from django.http import HttpResponse                                # ответы серверу (гитхабу)

from issues_linker.quickstart.models import Linked_Issues           # связанные issues

from issues_linker.my_functions import WRITE_LOG                    # ведение логов
from issues_linker.my_functions import align_special_symbols        # обработка спец. символов (\ -> \\)
from issues_linker.my_functions import read_file                    # загрузка файла (возвращает строку)

from issues_linker.my_functions import project_id_rm                # id преккта в редмайне
from issues_linker.my_functions import tracker_ids_rm               # ids трекеров задачи в редмайне
from issues_linker.my_functions import status_ids_rm                # ids статусов задачи в редмайне
from issues_linker.my_functions import priority_ids_rm              # ids приоритетов задачи в редмайне
from issues_linker.my_functions import url_rm                       # ссылка на сервер редмайна

from issues_linker.my_functions import chk_if_gh_user_is_our_bot    # проверка на бота (предотвращение
                                                                    # зацикливания: GH -> S -> RM -> ...)
from issues_linker.my_functions import log_issue_gh                 # лог связи issues
from issues_linker.my_functions import prevent_cyclic_issue_gh      # предотвращение зацикливания

from issues_linker.my_functions import match_label_to_rm            # сопостовление label-а в гитхабе редмайну

from issues_linker.my_functions import del_bot_phrase               # удаление фразы бота

from issues_linker.my_functions import allign_request_result        # создание корректного ответа серверу

from issues_linker.my_functions import match_tracker_to_gh          # сопоставление label-ов
from issues_linker.my_functions import match_status_to_gh           # сопоставление label-ов
from issues_linker.my_functions import match_priority_to_gh         # сопоставление label-ов
from issues_linker.my_functions import log_issue_edit_rm            # лог связи issues (изменение)
from issues_linker.my_functions import repos_id_gh                  # id репозитория в гитхабе
from issues_linker.my_functions import url_gh                       # ссылка на гитхаб

def process_payload_from_gh(payload):


    # =================================================== ПОДГОТОВКА ===================================================


    def parse_payload(payload):

        payload_parsed = {}  # словарь issue (название, описание, ссылка)

        # действие и его автор
        payload_parsed['action'] = payload['action']
        payload_parsed['sender_id'] = payload['sender']['id']  # sender - тот, кто совершил действие
        payload_parsed['sender_login'] = payload['sender']['login']

        # заполение полей issue
        payload_parsed['issue_title'] = payload['issue']['title']
        payload_parsed['issue_body'] = payload['issue']['body']
        payload_parsed['issue_author_id'] = payload['issue']['user']['id']
        payload_parsed['issue_author_login'] = payload['issue']['user']['login']

        # идентификаторы (для связи и логов)
        payload_parsed['issue_id'] = payload['issue']['id']
        payload_parsed['repos_id'] = payload['repository']['id']
        payload_parsed['issue_number'] = payload['issue']['number']

        # ссылка на issue (для фразы бота и логов)
        payload_parsed['issue_url'] = payload['issue']['html_url']

        payload_parsed['labels'] = payload['issue']['labels']

        if (payload_parsed['action'] == 'labeled'):
            payload_parsed['label'] = payload['label']['name']


        return payload_parsed

    issue = parse_payload(payload)

    # авторизация в redmine по токену
    api_key_redmime = read_file('api_keys/api_key_redmime_local.txt') # загрузка ключа для redmine api
    api_key_redmime = api_key_redmime.replace('\n', '')  # избавляемся от \n в конце строки

    # загрузка template из файла
    issue_redmine_template = read_file('parsed_data_templates/issue_redmine_template.json')
    issue_redmine_template = Template(issue_redmine_template)  # шаблон для каждого issue

    # заголовки авторизации и приложения, при отправке запросов на редмайн
    headers_rm = {'X-Redmine-API-Key': api_key_redmime,
                  'Content-Type': 'application/json'}


    # авторизация в гитхабе по токену
    api_key_github = read_file('api_keys/api_key_github.txt')   # загрузка ключа для github api
    api_key_github = api_key_github.replace('\n', '')  # избавляемся от \n в конце строки

    # загрузка issue template из файла
    issue_github_template = read_file('parsed_data_templates/issue_github_template.json')
    issue_github_template = Template(issue_github_template)  # шаблон для каждого issue

    # заголовки авторизации и приложения, при отправке запросов на гитхаб
    headers_gh = {'Authorization': 'token ' + api_key_github,
                  'Content-Type': 'application/json'}



    # ============================================= КОМАНДЫ ДЛЯ ЗАГРУЗКИ ===============================================


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

            author_url = '"' + issue['sender_login'] + '":' + 'https://github.com/' + issue['sender_login']
            issue_url = '"issue":' + issue['issue_url']
            comment_body = 'I am a bot, bleep-bloop.\n' +\
                         author_url + ' Has ' + issue['action'] + ' the ' + issue_url + ' in Github.'
                         #author_url + ' Has ' + issue['action'] + ' a comment on ' + issue_url + '.'

            return comment_body

        elif (to == 'comment_body_action'):

            author_url = '"' + issue['sender_login'] + '":' + 'https://github.com/' + issue['sender_login']
            issue_url = '"issue":' + issue['issue_url']
            comment_body = 'I am a bot, bleep-bloop.\n' +\
                         author_url + ' Has ' + issue['action'] + ' the ' + issue_url + ' in Github.'
                         #author_url + ' Has ' + issue['action'] + ' a comment on ' + issue_url + '.'

            return comment_body

        else:

            WRITE_LOG("\nERROR: process_payload_from_gh.add_bot_phrase - unknown parameter 'to': " + to + '.' +
                      "\nPlease, check your code on possible typos." +
                      "\nAlternatively, add logic to process '" + to + "' action correctly.\n")

            return None


    def correct_gh_labels(issue, tracker, linked_issues):

        # добавление label-ов
        tracker = tracker
        status = match_status_to_gh(linked_issues.status_id_rm)
        priority = match_priority_to_gh(linked_issues.priority_id_rm)


        # ----------------------------------------- ЗАГРУЖАЕМ ДАННЫЕ В ГИТХАБ ------------------------------------------


        issue_templated = issue_github_template.render(
            title = issue['issue_title'],
            body = issue['issue_body'],
            priority=priority,
            status=status,
            tracker=tracker)
        # кодировка Latin-1 на некоторых задачах приводит к ошибке кодировки в питоне
        issue_templated = issue_templated.encode('utf-8')

        # добавление issue_id к ссылке
        issue_url_gh = url_gh + '/' + str(linked_issues.issue_num_gh)
        request_result = requests.patch(issue_url_gh,
                                   data=issue_templated,
                                   headers=headers_gh)

        return request_result

    def post_issue(issue):


        # ------------------------------------------- ОБРАБАТЫВАЕМ ФРАЗУ БОТА ------------------------------------------


        #title = '[From Github] ' + issue['issue_title']
        title = issue['issue_title']
        issue_body = add_bot_phrase(issue, 'issue_body')   # добавляем фразу бота

        # обработка спец. символов
        title = align_special_symbols(title)
        issue_body = align_special_symbols(issue_body)


        # ----------------------------------------- ЗАГРУЖАЕМ ДАННЫЕ В РЕДМАЙН -----------------------------------------


        # Настраиваем label-ы
        tracker_id_rm = None
        status_id_rm = status_ids_rm[0]
        priority_id_rm = priority_ids_rm[0]
        for label in issue['labels']:
            tracker_rm = match_label_to_rm(label['name'])

            if (tracker_rm != None):
                if (tracker_rm['type'] == 'Tracker'):
                    if (tracker_id_rm == None):
                        tracker_id_rm = tracker_rm['id_rm']

        # TODO: отправлять label-ы в гитхаб + удалять лишние
        # проверяем, был ли установлен трекер
        if (tracker_id_rm == None):
            tracker_id_rm = tracker_ids_rm[0]


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


        # ---------------------------------------------- СВЯЗЫВАЕМ ISSUES ----------------------------------------------

        WRITE_LOG('\n'+str(tracker_id_rm)+'\n')
        # занесение в базу данных информацию о том, что данные issues связаны
        posted_issue = json.loads(request_result.text)
        linked_issues = Linked_Issues.objects.create_linked_issues(
            posted_issue['issue']['id'],    # id issue в редмайне
            issue['issue_id'],              # id issue в гитхабе
            issue['repos_id'],              # id репозитория в гитхабе
            issue['issue_number'],          # номер issue  в репозитории гитхаба
            tracker_id_rm,                  # id трекера в редмайне
            status_id_rm,                   # id статуса в редмайне
            priority_id_rm)                 # id приоритета в редмайне

        # добавляем label-ы в linked_issues
        linked_issues.tracker_id_rm = tracker_id_rm
        linked_issues.status_id_rm = status_id_rm
        linked_issues.priority_id_rm = priority_id_rm

        # корректируем label-ы в гитхабе
        tracker = match_tracker_to_gh(linked_issues.tracker_id_rm)
        correct_gh_labels(issue, tracker, linked_issues)


        # ДЕБАГГИНГ
        log_issue_gh(request_result, issue, linked_issues)

        return request_result

    def edit_issue(issue, linked_issues, status_id):

        # дополнительная проверка, что issue связаны
        # (на случай, если изменили не связанный issue)
        if (linked_issues.count() == 0):
            error_text = "ERROR: issue edited in GITHUB, but it's not linked to REDMINE"
            WRITE_LOG('\n' + '-'*20 + ' ' + str(datetime.datetime.today()) + ' | EDIT issue in REDMINE ' + '-'*19 + '\n' +
                      error_text)
            return HttpResponse(error_text, status=404)

        linked_issues = linked_issues[0]


        # ------------------------------------------- ОБРАБАТЫВАЕМ ФРАЗУ БОТА ------------------------------------------


        #title = '[From Github] ' + issue['issue_title']
        title = issue['issue_title']

        # проверяем, если автор issue - бот
        if (chk_if_gh_user_is_our_bot(issue['issue_author_id'])):
            issue_body = del_bot_phrase(issue['issue_body'])        # удаляем фразу бота

        else:
            issue_body = add_bot_phrase(issue, 'issue_body')        # добавляем фразу бота

        comment_body = add_bot_phrase(issue, 'comment_body_action') # добавляем фразу бота в комментарий к действию

        # обработка спец. символов
        title = align_special_symbols(title)
        issue_body = align_special_symbols(issue_body)
        comment_body = align_special_symbols(comment_body)


        # ----------------------------------------- ЗАГРУЖАЕМ ДАННЫЕ В РЕДМАЙН -----------------------------------------


        issue_templated = issue_redmine_template.render(
            project_id=project_id_rm,
            issue_id=linked_issues.issue_id_rm,
            tracker_id=linked_issues.tracker_id_rm,
            status_id=status_id,
            priority_id=linked_issues.priority_id_rm,
            subject=title,
            description=issue_body,
            notes=comment_body)

        # кодировка Latin-1 на некоторых задачах приводит к ошибке кодировки в питоне
        issue_templated = issue_templated.encode('utf-8')

        issue_url_rm = url_rm.replace('.json',
                                      '/' + str(linked_issues.issue_id_rm) + '.json')
        request_result = requests.put(issue_url_rm,
                                      data=issue_templated,
                                      headers=headers_rm)
        # ДЕБАГГИНГ
        log_issue_gh(request_result, issue, linked_issues)

        return request_result

    # TODO: не удалять, а ставить "rejected" в редмайне
    def delete_issue(issue, linked_issues):

        # УДАЛЯЕМ ИЗ РЕДМАЙНА
        # дополнительная проверка, что issue связаны
        # (на случай, если удалили не связанный issue)
        if (linked_issues.count() == 0):
            error_text = "ERROR: issue deleted in GITHUB, but it's not linked to REDMINE"
            WRITE_LOG('\n' + '-'*20 + ' ' + str(datetime.datetime.today()) + ' | EDIT issue in REDMINE ' + '-'*19 + '\n' +
                      error_text)
            return HttpResponse(error_text, status=404)

        linked_issues = linked_issues[0]

        issue_url_rm = url_rm.replace('.json',
                                      '/' + str(linked_issues.issue_id_rm) + '.json')

        request_result = requests.delete(issue_url_rm,
                                         headers=headers_rm)
        # ДЕБАГГИНГ
        log_issue_gh(request_result, issue, linked_issues)

        return request_result

    def label_issue(issue, linked_issues):

        label = match_label_to_rm(issue['label'])

        # дополнительная проверка, что issue связаны
        # (на случай, если изменили не связанный issue)
        if (linked_issues.count() == 0):
            error_text = "ERROR: issue edited in GITHUB, but it's not linked to REDMINE"
            WRITE_LOG('\n' + '-'*20 + ' ' + str(datetime.datetime.today()) + ' | EDIT issue in REDMINE ' + '-'*19 + '\n' +
                      error_text)
            return HttpResponse(error_text, status=404)

        linked_issues = linked_issues[0]


        # если неправильный label в гитхабе -> значения по умлчанию
        tracker_id = linked_issues.tracker_id_rm
        if (label != None):
            if (label['type'] == 'Priority'):

                # корректируем label-ы в гитхабе
                tracker = match_tracker_to_gh(tracker_id)
                correct_gh_labels(issue, tracker, linked_issues)

                error_text = "ERROR: tried to LABEL issue's PRIORITY from GITHUB"
                WRITE_LOG('\n' + '-' * 20 + ' ' + str(
                    datetime.datetime.today()) + ' | EDIT issue in REDMINE ' + '-' * 19 + '\n' +
                          error_text)

                return HttpResponse(error_text, status=403)

            elif (label['type'] == 'Status'):

                # корректируем label-ы в гитхабе
                tracker = match_tracker_to_gh(tracker_id)
                correct_gh_labels(issue, tracker, linked_issues)

                error_text = "ERROR: tried to LABEL issue's STATUS from GITHUB"
                WRITE_LOG('\n' + '-' * 20 + ' ' + str(
                    datetime.datetime.today()) + ' | EDIT issue in REDMINE ' + '-' * 19 + '\n' +
                          error_text)

                return HttpResponse(error_text, status=403)

            elif (label['type'] == 'Tracker'):

                tracker_id = label['id_rm']
                linked_issues.tracker_id_rm = tracker_id


        # ------------------------------------------- ОБРАБАТЫВАЕМ ФРАЗУ БОТА ------------------------------------------


        #title = '[From Github] ' + issue['issue_title']
        title = issue['issue_title']

        # проверяем, если автор issue - бот
        if (chk_if_gh_user_is_our_bot(issue['issue_author_id'])):
            issue_body = del_bot_phrase(issue['issue_body'])        # удаляем фразу бота

        else:
            issue_body = add_bot_phrase(issue, 'issue_body')        # добавляем фразу бота

        comment_body = add_bot_phrase(issue, 'comment_body_action') # добавляем фразу бота в комментарий к действию

        # обработка спец. символов
        title = align_special_symbols(title)
        issue_body = align_special_symbols(issue_body)
        comment_body = align_special_symbols(comment_body)


        # ----------------------------------------- ЗАГРУЖАЕМ ДАННЫЕ В РЕДМАЙН -----------------------------------------


        issue_templated = issue_redmine_template.render(
            project_id=project_id_rm,
            issue_id=linked_issues.issue_id_rm,
            tracker_id=tracker_id,
            status_id=linked_issues.status_id_rm,
            priority_id=linked_issues.priority_id_rm,
            subject=title,
            description=issue_body,
            notes=comment_body)

        # кодировка Latin-1 на некоторых задачах приводит к ошибке кодировки в питоне
        issue_templated = issue_templated.encode('utf-8')

        issue_url_rm = url_rm.replace('.json',
                                      '/' + str(linked_issues.issue_id_rm) + '.json')
        request_result = requests.put(issue_url_rm,
                                      data=issue_templated,
                                      headers=headers_rm)
        # ДЕБАГГИНГ
        log_issue_gh(request_result, issue, linked_issues)

        # корректируем label-ы в гитхабе
        correct_gh_labels(issue, issue['label'], linked_issues)

        return request_result


    # ============================================ ЗАГРУЗКА ISSUE В REDMINE ============================================


    linked_issues = Linked_Issues.objects.get_by_issue_id_gh(issue['issue_id'])
    if (issue['action'] == 'opened'):

        if (chk_if_gh_user_is_our_bot(issue['sender_id'])):

            error_text = prevent_cyclic_issue_gh(issue)
            return HttpResponse(error_text, status=200)

        request_result = post_issue(issue)

    elif (issue['action'] == 'edited'):

        if (chk_if_gh_user_is_our_bot(issue['sender_id'])):

            error_text = prevent_cyclic_issue_gh(issue)
            return HttpResponse(error_text, status=200)

        request_result = edit_issue(issue, linked_issues, status_ids_rm[0])      # 0 - status "new"

    elif (issue['action'] == 'closed'):

        if (chk_if_gh_user_is_our_bot(issue['sender_id'])):

            error_text = prevent_cyclic_issue_gh(issue)
            return HttpResponse(error_text, status=200)

        request_result = edit_issue(issue, linked_issues, status_ids_rm[5])      # 5 - status "closed"

    elif (issue['action'] == 'reopened'):

        if (chk_if_gh_user_is_our_bot(issue['sender_id'])):

            error_text = prevent_cyclic_issue_gh(issue)
            return HttpResponse(error_text, status=200)

        request_result = edit_issue(issue, linked_issues, status_ids_rm[0])      # 0 - status "new"

    elif (issue['action'] == 'deleted'):

        if (chk_if_gh_user_is_our_bot(issue['sender_id'])):

            error_text = prevent_cyclic_issue_gh(issue)
            return HttpResponse(error_text, status=200)

        request_result = delete_issue(issue, linked_issues)

    elif (issue['action'] == 'labeled'):

        if (chk_if_gh_user_is_our_bot(issue['sender_id'])):

            error_text = prevent_cyclic_issue_gh(issue)
            return HttpResponse(error_text, status=200)

        request_result = label_issue(issue, linked_issues)

    else:
        error_text = 'ERROR: WRONG ACTION'
        WRITE_LOG('\n' + '='*35 + ' ' + str(datetime.datetime.today()) + ' ' + '='*35 + '\n' +
                  'received webhook from GITHUB: issues | ' + 'action: ' + str(issue['action']) + '\n' +
                  error_text)
        return HttpResponse(error_text, status=422)


    return allign_request_result(request_result)
