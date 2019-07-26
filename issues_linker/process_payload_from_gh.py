import requests
import datetime
from jinja2 import Template
import json
from django.http import HttpResponse                            # ответы серверу (гитхабу)

from issues_linker.quickstart.models import Linked_Issues       # связанные issues

from issues_linker.my_functions import WRITE_LOG                # ведение логов
from issues_linker.my_functions import align_special_symbols    # обработка спец. символов (\ -> \\)
from issues_linker.my_functions import read_file                # загрузка файла (возвращает строку)

from issues_linker.my_functions import project_id_rm            # id преккта в редмайне
from issues_linker.my_functions import tracker_ids_rm           # ids трекеров задачи в редмайне
from issues_linker.my_functions import status_ids_rm            # ids статусов задачи в редмайне
from issues_linker.my_functions import priority_ids_rm          # ids приоритетов задачи в редмайне
from issues_linker.my_functions import url_rm                   # ссылка на сервер редмайна

from issues_linker.my_functions import chk_if_gh_user_is_a_bot  # проверка на бота (предотвращение
                                                                # зацикливания: GH -> S -> RM -> ...)
from issues_linker.my_functions import link_log_issue_gh        # лог связи issues
from issues_linker.my_functions import prevent_cyclic_issue_gh  # предотвращение зацикливания

from issues_linker.my_functions import match_label_to_rm        # сопостовление label-а в гитхабе редмайну

from issues_linker.my_functions import del_bot_phrase           # удаление фразы бота

from issues_linker.my_functions import allign_request_result    # создание корректного ответа серверу


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
    headers = {'X-Redmine-API-Key': api_key_redmime,
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
                         author_url_gh + ' Has opened an ' + issue_url_gh + ' in Github'
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

        else:

            WRITE_LOG("\nERROR: process_payload_from_gh.add_bot_phrase - unknown parameter 'to': " + to + '.' +
                      "\nPlease, check your code on possible typos." +
                      "\nAlternatively, add logic to process '" + to + "' action correctly.\n")

            return None


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
        labels_rm = {}
        labels_rm['Приоритет'] = None
        labels_rm['Статус'] = None
        labels_rm['Трекер'] = None
        for label in issue['labels']:
            label_rm = match_label_to_rm(label['name'])

            if (label_rm != None):
                if (label_rm['type'] == 'Приоритет'):
                    if (labels_rm['Приоритет'] == None):
                        labels_rm['Приоритет'] = label_rm['id_rm']

                elif (label_rm['type'] == 'Статус'):
                    if (labels_rm['Статус'] == None):
                        labels_rm['Статус'] = label_rm['id_rm']

                elif (label_rm['type'] == 'Трекер'):
                    if (labels_rm['Трекер'] == None):
                        labels_rm['Трекер'] = label_rm['id_rm']

        # TODO: отправлять label-ы в гитхаб + удалять лишние
        # проверяем, все ли label-ы были установлены
        if (labels_rm['Приоритет'] == None):
            labels_rm['Приоритет'] = priority_ids_rm[0]

        if (labels_rm['Статус'] == None):
            labels_rm['Статус'] = status_ids_rm[0]

        if (labels_rm['Трекер'] == None):
            labels_rm['Трекер'] = tracker_ids_rm[0]


        issue_templated = issue_redmine_template.render(
            project_id=project_id_rm,
            tracker_id=labels_rm['Трекер'],
            status_id=labels_rm['Статус'],
            priority_id=labels_rm['Приоритет'],
            subject=title,
            description=issue_body)

        # кодировка по умолчанию (Latin-1) на некоторых задачах приводит к ошибке кодировки в питоне
        issue_templated = issue_templated.encode('utf-8')

        request_result = requests.post(url_rm,
                                       data=issue_templated,
                                       headers=headers)


        # ---------------------------------------------- СВЯЗЫВАЕМ ISSUES ----------------------------------------------


        # занесение в базу данных информацию о том, что данные issues связаны
        posted_issue = json.loads(request_result.text)
        linked_issues = Linked_Issues.objects.create_linked_issues(
            posted_issue['issue']['id'],    # id issue в редмайне
            issue['issue_id'],              # id issue в гитхабе
            issue['repos_id'],              # id репозитория в гитхабе
            issue['issue_number'])          # номер issue  в репозитории гитхаба

        # добавляем label-ы в linked_issues
        WRITE_LOG('\n'+str(labels_rm['Приоритет'])+'\n'+str(labels_rm['Статус'])+'\n'+str(labels_rm['Трекер'])+'\n')
        linked_issues.set_priority(labels_rm['Приоритет'])
        linked_issues.set_status(labels_rm['Статус'])
        linked_issues.set_tracker(labels_rm['Трекер'])

        # ДЕБАГГИНГ
        link_log_issue_gh(request_result, issue, linked_issues)

        '''
        # Настраиваем label-ы
        for label in issue['labels']:
            label_rm = match_label_to_rm(label['name'])
            label_issue(issue, linked_issues, label_rm)
        
        # TODO: отправлять label-ы в гитхаб
        # проверяем, все ли label-ы были установлены
        if (linked_issues.get_tracker() == None):
            linked_issues.set_tracker(tracker_ids_rm[0])
            
        if (linked_issues.get_status() == None):
            linked_issues.set_status(status_ids_rm[0])

        if (linked_issues.get_priority() == None):
            linked_issues.set_priority(priority_ids_rm[0])
            '''

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
        if (chk_if_gh_user_is_a_bot(issue['issue_author_id'])):
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
            tracker_id=tracker_ids_rm[0],
            status_id=status_id,
            priority_id=priority_ids_rm[0],
            subject=title,
            description=issue_body,
            notes=comment_body)

        # кодировка Latin-1 на некоторых задачах приводит к ошибке кодировки в питоне
        issue_templated = issue_templated.encode('utf-8')

        issue_url_rm = url_rm.replace('.json',
                                      '/' + str(linked_issues.issue_id_rm) + '.json')
        request_result = requests.put(issue_url_rm,
                                      data=issue_templated,
                                      headers=headers)
        # ДЕБАГГИНГ
        link_log_issue_gh(request_result, issue, linked_issues)

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
                                         headers=headers)
        # ДЕБАГГИНГ
        link_log_issue_gh(request_result, issue, linked_issues)

        return request_result

    def label_issue(issue, linked_issues, label):

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
        if (chk_if_gh_user_is_a_bot(issue['issue_author_id'])):
            issue_body = del_bot_phrase(issue['issue_body'])        # удаляем фразу бота

        else:
            issue_body = add_bot_phrase(issue, 'issue_body')        # добавляем фразу бота

        comment_body = add_bot_phrase(issue, 'comment_body_action') # добавляем фразу бота в комментарий к действию

        # обработка спец. символов
        title = align_special_symbols(title)
        issue_body = align_special_symbols(issue_body)
        comment_body = align_special_symbols(comment_body)


        # ----------------------------------------- ЗАГРУЖАЕМ ДАННЫЕ В РЕДМАЙН -----------------------------------------


        # если неправильный label в гитхабе -> значения по умлчанию
        tracker_id = linked_issues.get_tracker()
        status_id = linked_issues.get_status()
        priority_id = linked_issues.get_priority()
        if (label != None):
            if (label['type'] == 'Приоритет'):
                if (priority_id != None):
                    error_text = "ERROR: tried to LABEL issue's PRIORITY, but it's already labeled"
                    WRITE_LOG('\n' + '-'*20 + ' ' + str(datetime.datetime.today()) + ' | EDIT issue in REDMINE ' + '-'*19 + '\n' +
                              error_text)
                    return HttpResponse(error_text, status=404)

                priority_id = label['id_rm']
                linked_issues.set_priority(priority_id)

            elif (label['type'] == 'Статус'):
                if (priority_id != None):
                    error_text = "ERROR: tried to LABEL issue's STATUS, but it's already labeled"
                    WRITE_LOG('\n' + '-'*20 + ' ' + str(datetime.datetime.today()) + ' | EDIT issue in REDMINE ' + '-'*19 + '\n' +
                              error_text)
                    return HttpResponse(error_text, status=404)

                status_id = label['id_rm']
                linked_issues.set_status(status_id)

            elif (label['type'] == 'Трекер'):
                if (priority_id != None):
                    error_text = "ERROR: tried to LABEL issue's TRACKER, but it's already labeled"
                    WRITE_LOG('\n' + '-'*20 + ' ' + str(datetime.datetime.today()) + ' | EDIT issue in REDMINE ' + '-'*19 + '\n' +
                              error_text)
                    return HttpResponse(error_text, status=404)

                tracker_id = label['id_rm']
                linked_issues.set_tracker(tracker_id)


        issue_templated = issue_redmine_template.render(
            project_id=project_id_rm,
            issue_id=linked_issues.issue_id_rm,
            tracker_id=tracker_id,
            status_id=status_id,
            priority_id=priority_id,
            subject=title,
            description=issue_body,
            notes=comment_body)

        # кодировка Latin-1 на некоторых задачах приводит к ошибке кодировки в питоне
        issue_templated = issue_templated.encode('utf-8')

        issue_url_rm = url_rm.replace('.json',
                                      '/' + str(linked_issues.issue_id_rm) + '.json')
        request_result = requests.put(issue_url_rm,
                                      data=issue_templated,
                                      headers=headers)
        # ДЕБАГГИНГ
        link_log_issue_gh(request_result, issue, linked_issues)

        return request_result

    # ============================================ ЗАГРУЗКА ISSUE В REDMINE ============================================


    linked_issues = Linked_Issues.objects.get_by_issue_id_gh(issue['issue_id'])
    if (issue['action'] == 'opened'):

        if (chk_if_gh_user_is_a_bot(issue['sender_id'])):

            error_text = prevent_cyclic_issue_gh(issue)
            return HttpResponse(error_text, status=200)

        request_result = post_issue(issue)

    elif (issue['action'] == 'edited'):

        if (chk_if_gh_user_is_a_bot(issue['sender_id'])):

            error_text = prevent_cyclic_issue_gh(issue)
            return HttpResponse(error_text, status=200)

        request_result = edit_issue(issue, linked_issues, status_ids_rm[0])      # 0 - status "new"

    elif (issue['action'] == 'closed'):

        if (chk_if_gh_user_is_a_bot(issue['sender_id'])):

            error_text = prevent_cyclic_issue_gh(issue)
            return HttpResponse(error_text, status=200)

        request_result = edit_issue(issue, linked_issues, status_ids_rm[5])      # 5 - status "closed"

    elif (issue['action'] == 'reopened'):

        if (chk_if_gh_user_is_a_bot(issue['sender_id'])):

            error_text = prevent_cyclic_issue_gh(issue)
            return HttpResponse(error_text, status=200)

        request_result = edit_issue(issue, linked_issues, status_ids_rm[0])      # 0 - status "new"

    elif (issue['action'] == 'deleted'):

        if (chk_if_gh_user_is_a_bot(issue['sender_id'])):

            error_text = prevent_cyclic_issue_gh(issue)
            return HttpResponse(error_text, status=200)

        request_result = delete_issue(issue, linked_issues)

    elif (issue['action'] == 'labeled'):

        if (chk_if_gh_user_is_a_bot(issue['sender_id'])):

            error_text = prevent_cyclic_issue_gh(issue)
            return HttpResponse(error_text, status=200)

        label_rm = match_label_to_rm(issue['label'])

        request_result = label_issue(issue, linked_issues, label_rm)

    else:
        error_text = 'ERROR: WRONG ACTION'
        WRITE_LOG('\n' + '='*35 + ' ' + str(datetime.datetime.today()) + ' ' + '='*35 + '\n' +
                  'received webhook from GITHUB: issues | ' + 'action: ' + str(issue['action']) + '\n' +
                  error_text)
        return HttpResponse(error_text, status=422)


    return allign_request_result(request_result)
