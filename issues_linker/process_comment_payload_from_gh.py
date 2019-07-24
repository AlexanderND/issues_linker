import requests
import datetime
from jinja2 import Template
import json
from django.http import HttpResponse                            # ответы серверу (гитхабу)

from issues_linker.quickstart.models import Linked_Issues       # поиск связанных issues
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
from issues_linker.my_functions import link_log_comment_gh      # лог связи комментариев
from issues_linker.my_functions import prevent_cyclic_comment_gh    # предотвращение зацикливания


def process_comment_payload_from_gh(payload):


    # =================================================== ПОДГОТОВКА ===================================================


    def parse_payload(payload):
        payload = json.loads(payload['payload'])    # достаём содержимое payload

        payload_parsed = {}  # словарь issue (название, описание, ссылка)

        # действие и его автор
        payload_parsed['action'] = payload['action']
        payload_parsed['user_id'] = payload['sender']['id']  # sender - тот, кто совершил действие
        payload_parsed['user_login'] = payload['sender']['login']

        # заполение полей issue
        payload_parsed['title'] = payload['issue']['title']
        payload_parsed['body'] = payload['issue']['body']
        payload_parsed['issue_author_id'] = payload['issue']['user']['id']  # автор issue

        # идентификаторы (для связи и логов)
        payload_parsed['issue_id'] = payload['issue']['id']
        payload_parsed['repos_id'] = payload['repository']['id']
        payload_parsed['issue_number'] = payload['issue']['number']

        # ссылка на issue (для фразы бота и логов)
        payload_parsed['issue_url'] = payload['issue']['html_url']

        # комментарий
        payload_parsed['comment_body'] = payload['comment']['body']
        payload_parsed['comment_id'] = payload['comment']['id']

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


    # добавляем фразу бота к комментарию, со ссылкой на аккаунт пользователя в гитхабе
    def bot_speech_comment(issue):
        user_url = '"' + issue['user_login'] + '":' + 'https://github.com/' + issue['user_login']
        issue_url = '"Github":' + issue['issue_url']
        comment_body = 'I am a bot, bleep-bloop.\n' +\
                     user_url + ' Has left a comment on ' + issue_url + ': \n\n' + issue['comment_body']
                     #user_url + ' Has ' + issue['action'] + ' a comment on ' + issue_url + ': \n\n' + issue['comment_body']

        return comment_body


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
            # удаляем фразу бота
            bot_phrase, sep, issue_body = issue['body'].partition(':')
        else:
            issue_body = issue['body']

        comment_body = bot_speech_comment(issue)    # добавляем фразу бота

        # обработка спец. символов
        issue_title = align_special_symbols(issue['title'])
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
        # ДЕБАГГИНГ
        link_log_comment_gh(request_result, issue, linked_issues)

        return request_result


    # ============================================ ЗАГРУЗКА ISSUE В REDMINE ============================================


    linked_issues = Linked_Issues.objects.get_by_issue_id_gh(issue['issue_id'])
    if (issue['action'] == 'created'):

        if (chk_if_gh_user_is_a_bot(issue['user_id'])):

            error_text = prevent_cyclic_comment_gh(issue)
            return HttpResponse(error_text, status=200)

        request_result = post_comment(issue, linked_issues)

    else:
        error_text = 'ERROR: WRONG ACTION'
        WRITE_LOG('\n' + '='*35 + ' ' + str(datetime.datetime.today()) + ' ' + '='*35 + '\n' +
                  'received webhook from GITHUB: issue_comment | ' + 'action: ' + str(issue['action']) + '\n' +
                  error_text)
        return HttpResponse(error_text, status=422)

    request_result = HttpResponse(request_result.text, status=request_result.status_code)
    return request_result
