import requests
import datetime
from jinja2 import Template
import json
from django.http import HttpResponse                                # ответы серверу (гитхабу)

from issues_linker.quickstart.models import Linked_Issues           # связанные issues
from issues_linker.quickstart.models import Linked_Comments         # связанные комментарии

from issues_linker.my_functions import WRITE_LOG                    # ведение логов
from issues_linker.my_functions import align_special_symbols        # обработка спец. символов (\ -> \\)
from issues_linker.my_functions import read_file                    # загрузка файла (возвращает строку)

from issues_linker.my_functions import project_id_rm                # id преккта в редмайне
from issues_linker.my_functions import tracker_ids_rm               # ids трекеров задачи в редмайне
from issues_linker.my_functions import status_ids_rm                # ids статусов задачи в редмайне
from issues_linker.my_functions import priority_ids_rm              # ids приоритетов задачи в редмайне
from issues_linker.my_functions import url_rm                       # ссылка на сервер редмайна

from issues_linker.my_functions import chk_if_gh_user_is_a_bot      # проверка на бота (предотвращение
                                                                    # зацикливания: GH -> S -> RM -> ...)
from issues_linker.my_functions import link_log_comment_gh          # лог связи комментариев
from issues_linker.my_functions import prevent_cyclic_comment_gh    # предотвращение зацикливания

from issues_linker.my_functions import del_bot_phrase               # удаление фразы бота

from issues_linker.my_functions import allign_request_result    # создание корректного ответа серверу


def process_comment_payload_from_gh(payload):
    payload = json.loads(payload['payload'])    # достаём содержимое payload


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
        payload_parsed['issue_author_id'] = payload['issue']['user']['id']  # автор issue
        payload_parsed['issue_author_login'] = payload['issue']['user']['login']

        # идентификаторы (для связи и логов)
        payload_parsed['issue_id'] = payload['issue']['id']
        payload_parsed['repos_id'] = payload['repository']['id']
        payload_parsed['issue_number'] = payload['issue']['number']

        # ссылка на issue (для фразы бота и логов)
        payload_parsed['issue_url'] = payload['issue']['html_url']

        # комментарий
        payload_parsed['comment_body'] = payload['comment']['body']
        payload_parsed['comment_id'] = payload['comment']['id']
        payload_parsed['comment_author_id'] = payload['comment']['user']['id']
        payload_parsed['comment_author_login'] = payload['comment']['user']['login']

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
    # comment_body
    # добавляем фразу бота, со ссылкой на аккаунт пользователя в гитхабе
    def add_bot_phrase(issue, to):

        # добавляем фразу бота к описанию issue
        if (to == 'issue_body'):
            author_url_gh = '"' + issue['issue_author_login'] + '":' + 'https://github.com/' + issue['issue_author_login']
            issue_url_gh = '"issue on Github":' + issue['issue_url']
            issue_body = 'I am a bot, bleep-bloop.\n' +\
                         author_url_gh + ' Has opened an ' + issue_url_gh
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

        # добавляем фразу бота к комментарию
        elif (to == 'comment_body'):

            # добавляем цитирование
            comment_body = issue['comment_body'].replace('\n', '\n>')
            comment_body = '>' + comment_body

            # добавляем фразу бота
            author_url = '"' + issue['comment_author_login'] + '":' + 'https://github.com/' + issue['comment_author_login']
            comment_url = '"comment on Github":' + issue['issue_url'] + '#issuecomment-' + str(issue['comment_id'])
            comment_body = 'I am a bot, bleep-bloop.\n' +\
                           author_url + ' Has left a ' + comment_url + ': \n\n' + comment_body

            return comment_body

        else:

            WRITE_LOG("\nERROR: process_comment_payload_from_gh.add_bot_phrase - unknown parameter 'to': " + to + '.' +
                      "\nPlease, check your code on possible typos." +
                      "\nAlternatively, add logic to process '" + to + "' action correctly.")

            return None


    def post_comment(issue, linked_issues):

        # дополнительная проверка, что issue связаны
        # (на случай, если изменили не связанный issue)
        if (linked_issues.count() == 0):
            WRITE_LOG('\n' + '='*35 + ' ' + str(datetime.datetime.today()) + ' ' + '='*35 + '\n' +
                      'received webhook from GITHUB: issue_comments | ' + 'action: ' + str(issue['action']) + '\n' +
                      "ERROR: posted comment on GITHUB, but the issue is not linked to REDMINE")
            return HttpResponse(status=404)
        linked_issues = linked_issues[0]


        # ------------------------------------------- ОБРАБАТЫВАЕМ ФРАЗУ БОТА ------------------------------------------


        # проверяем, если автор issue - бот
        if (chk_if_gh_user_is_a_bot(issue['issue_author_id'])):
            issue_body = del_bot_phrase(issue['issue_body'])

        else:
            issue_body = add_bot_phrase(issue, 'issue_body')

        comment_body = add_bot_phrase(issue, 'comment_body')    # добавляем фразу бота

        # обработка спец. символов
        issue_title = align_special_symbols(issue['issue_title'])
        issue_body = align_special_symbols(issue_body)
        comment_body = align_special_symbols(comment_body)


        # ----------------------------------------- ЗАГРУЖАЕМ ДАННЫЕ В РЕДМАЙН -----------------------------------------


        issue_templated = issue_redmine_template.render(
            project_id=project_id_rm,
            issue_id=linked_issues.issue_id_rm,
            priority_id=priority_ids_rm[0],
            subject=issue_title,
            description=issue_body,
            notes=comment_body)

        # кодировка Latin-1 на некоторых задачах приводит к ошибке кодировки в питоне
        issue_templated = issue_templated.encode('utf-8')

        issue_url_rm = url_rm.replace('.json',
                                      '/' + str(linked_issues.issue_id_rm) + '.json')
        request_result = requests.put(issue_url_rm,
                                      data=issue_templated,
                                      headers=headers)


        # ------------------------------------------- ПРИВЯЗКА КОММЕНТАРИЕВ --------------------------------------------
        # (делаем привязку после получения веб-хука от редмайна)


        # ДЕБАГГИНГ
        link_log_comment_gh(request_result, issue, linked_issues)

        return request_result

    '''def edit_comment(issue, linked_issues):

        # дополнительная проверка, что issue связаны
        # (на случай, если изменили не связанный issue)
        if (linked_issues.count() == 0):
            WRITE_LOG('\n' + '='*35 + ' ' + str(datetime.datetime.today()) + ' ' + '='*35 + '\n' +
                      'received webhook from GITHUB: issue_comments | ' + 'action: ' + str(issue['action']) + '\n' +
                      "ERROR: posted comment on GITHUB, but the issue is not linked to REDMINE")
            return HttpResponse(status=404)
        linked_issues = linked_issues[0]

        # дополнительная проверка, что комментарии связаны
        linked_comments = linked_issues.get_comment_by_id_gh(issue['comment_id'])
        if (linked_comments.count() == 0):
            WRITE_LOG('\n' + '='*35 + ' ' + str(datetime.datetime.today()) + ' ' + '='*35 + '\n' +
                      'received webhook from GITHUB: issue_comments | ' + 'action: ' + str(issue['action']) + '\n' +
                      "ERROR: edited comment on GITHUB, but it is not linked to REDMINE")
            return HttpResponse(status=404)
        linked_comments = linked_comments[0]


        # ------------------------------------------- ОБРАБАТЫВАЕМ ФРАЗУ БОТА ------------------------------------------


        # проверяем, если автор issue - бот
        if (chk_if_gh_user_is_a_bot(issue['issue_author_id'])):
            issue_body = del_bot_phrase(issue['issue_body'])

        else:
            issue_body = add_bot_phrase(issue)

        comment_body = bot_speech_comment(issue)    # добавляем фразу бота

        # обработка спец. символов
        issue_title = align_special_symbols(issue['issue_title'])
        issue_body = align_special_symbols(issue_body)
        comment_body = align_special_symbols(comment_body)


        # ----------------------------------------- ЗАГРУЖАЕМ ДАННЫЕ В РЕДМАЙН -----------------------------------------


        issue_templated = issue_redmine_template.render(
            project_id=project_id_rm,
            issue_id=linked_issues.issue_id_rm,
            priority_id=priority_ids_rm[0],
            subject=issue_title,
            description=issue_body,
            notes=comment_body)

        # кодировка Latin-1 на некоторых задачах приводит к ошибке кодировки в питоне
        issue_templated = issue_templated.encode('utf-8')

        issue_url_rm = url_rm.replace('.json',
                                      '/' + str(linked_issues.issue_id_rm) + '.json')
        request_result = requests.put(issue_url_rm,
                                      data=issue_templated,
                                      headers=headers)


        # ------------------------------------------- ПРИВЯЗКА КОММЕНТАРИЕВ --------------------------------------------
        # (делаем привязку после получения веб-хука от редмайна)


        # ДЕБАГГИНГ
        link_log_comment_gh(request_result, issue, linked_issues)

        return request_result'''


    # ========================================= ЗАГРУЗКА КОММЕНТАРИЯ В REDMINE =========================================


    linked_issues = Linked_Issues.objects.get_by_issue_id_gh(issue['issue_id'])
    if (issue['action'] == 'created'):

        if (chk_if_gh_user_is_a_bot(issue['sender_id'])):

            error_text = prevent_cyclic_comment_gh(issue)
            return HttpResponse(error_text, status=200)

        request_result = post_comment(issue, linked_issues)

        '''elif (issue['action'] == 'edited'):
    
            if (chk_if_gh_user_is_a_bot(issue['sender_id'])):
    
                error_text = prevent_cyclic_comment_gh(issue)
                return HttpResponse(error_text, status=200)
    
            request_result = edit_comment(issue, linked_issues)
            #request_result = post_comment(issue, linked_issues)'''

    else:
        error_text = 'ERROR: WRONG ACTION'
        WRITE_LOG('\n' + '='*35 + ' ' + str(datetime.datetime.today()) + ' ' + '='*35 + '\n' +
                  'received webhook from GITHUB: issue_comment | ' + 'action: ' + str(issue['action']) + '\n' +
                  error_text)
        return HttpResponse(error_text, status=422)


    return allign_request_result(request_result)
