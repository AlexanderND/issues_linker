import requests
import datetime
from jinja2 import Template
import json
from django.http import HttpResponse                                # ответы серверу (редмайну)

from issues_linker.quickstart.models import Linked_Issues           # связанные issues
from issues_linker.quickstart.models import Linked_Comments         # связанные комментарии

from issues_linker.my_functions import WRITE_LOG                    # ведение логов
from issues_linker.my_functions import align_special_symbols        # обработка спец. символов (\ -> \\)
from issues_linker.my_functions import read_file                    # загрузка файла (возвращает строку)

from issues_linker.my_functions import repos_id_gh                  # id репозитория в гитхабе
from issues_linker.my_functions import url_gh                       # ссылка на гитхаб

from issues_linker.my_functions import chk_if_rm_user_is_a_bot      # проверка на бота (предотвращение
                                                                    # зацикливания: RM -> S -> GH -> ...)
from issues_linker.my_functions import link_log_rm_post             # лог связи issues (создание)
from issues_linker.my_functions import link_log_rm_edit             # лог связи issues (изменение)
from issues_linker.my_functions import link_log_rm_comment          # лог связи issues (комментарий)
from issues_linker.my_functions import prevent_cyclic_issue_rm      # предотвращение зацикливания issue
from issues_linker.my_functions import prevent_cyclic_comment_rm    # предотвращение зацикливания комментариев

from issues_linker.my_functions import del_bot_phrase               # удаление фразы бота

from issues_linker.my_functions import allign_request_result    # создание корректного ответа серверу


def process_payload_from_rm(payload):
    payload = payload['payload']    # достаём содержимое payload. payload payload. payload?


    # =================================================== ПОДГОТОВКА ===================================================


    def parse_payload(payload):

        payload_parsed = {}  # словарь issue (название, описание, ссылка)

        # автор issue
        payload_parsed['issue_author_id'] = payload['issue']['author']['id']
        payload_parsed['issue_author_login'] = payload['issue']['author']['login']
        payload_parsed['issue_author_firstname'] = payload['issue']['author']['firstname']
        payload_parsed['issue_author_lastname'] = payload['issue']['author']['lastname']

        payload_parsed['action'] = payload['action']    # совершённое действие

        # при update возможна добавка комментария
        if (payload_parsed['action'] == 'updated'):

            # тело комментария
            payload_parsed['comment_body'] = payload['journal']['notes']

            # id комментария (для связи и логов)
            payload_parsed['comment_id'] = payload['journal']['id']

            # автор комментария
            payload_parsed['comment_author_id'] = payload['journal']['author']['id']
            payload_parsed['comment_author_login'] = payload['journal']['author']['login']
            payload_parsed['comment_author_firstname'] = payload['journal']['author']['firstname']
            payload_parsed['comment_author_lastname'] = payload['journal']['author']['lastname']

        # заполение полей issue
        payload_parsed['issue_title'] = payload['issue']['subject']
        payload_parsed['issue_body'] = payload['issue']['description']
        payload_parsed['status_id'] = payload['issue']['status']['id']

        # идентификаторы (для связи и логов)
        payload_parsed['issue_id'] = payload['issue']['id']
        payload_parsed['project_id'] = payload['issue']['project']['id']

        # ссылка на issue (для фразы бота и логов)
        payload_parsed['issue_url'] = payload['url']

        return payload_parsed

    issue = parse_payload(payload)

    # авторизация в redmine по токену
    api_key_github = read_file('api_keys/api_key_github.txt')   # загрузка ключа для github api
    api_key_github = api_key_github.replace('\n', '')  # избавляемся от \n в конце строки

    # загрузка issue template из файла
    issue_github_template = read_file('parsed_data_templates/issue_github_template.json')
    issue_github_template = Template(issue_github_template)  # шаблон для каждого issue

    # загрузка comment template из файла
    comment_github_template = read_file('parsed_data_templates/comment_github_template.json')
    comment_github_template = Template(comment_github_template)  # шаблон для каждого issue

    # заголовки авторизации и приложения, при отправке запросов на редмайн
    headers = {'Authorization': 'token ' + api_key_github,
               'Content-Type': 'application/json'}


    # ============================================= КОМАНДЫ ДЛЯ ЗАГРУЗКИ ===============================================


    # issue_body
    # comment_body
    # comment_body_action
    # добавляем фразу бота
    def add_bot_phrase(issue, to):

        # добавляем фразу бота к описанию issue
        if (to == 'issue_body'):
            # добавляем фразу бота
            issue_body = 'I am a bot, bleep-bloop.\n' +\
                         issue['issue_author_firstname'] + ' ' +\
                         issue['issue_author_lastname'] + ' (' +\
                         issue['issue_author_login'] +\
                         ') Has opened the issue in Redmine'

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
            comment_body = 'I am a bot, bleep-bloop.\n' + \
                           issue['comment_author_firstname'] + ' ' + \
                           issue['comment_author_lastname'] + ' (' + \
                           issue['comment_author_login'] + \
                           ') Has commented / edited with comment the issue in Redmine: \n\n' + \
                           comment_body

            return comment_body

        # добавляем фразу бота (комментарием) к действию в редмайне (закрыл, изменил и т.д.)
        elif (to == 'comment_body_action'):

            # добавляем фразу бота
            comment_body = 'I am a bot, bleep-bloop.\n' + \
                           issue['comment_author_firstname'] + ' ' + \
                           issue['comment_author_lastname'] + ' (' + \
                           issue['comment_author_login'] + \
                           ') Has edited the issue in Redmine.'

            return comment_body

        else:

            WRITE_LOG("\nERROR: process_payload_from_rm.add_bot_phrase - unknown parameter 'to': " + to + '.' +
                      "\nPlease, check your code on possible typos." +
                      "\nAlternatively, add logic to process '" + to + "' action correctly.")

            return None


    def post_issue(issue):

        #title = '[From Redmine] ' + issue['issue_title']
        title = issue['issue_title']
        issue_body = add_bot_phrase(issue, 'issue_body')     # добавляем фразу бота

        # обработка спец. символов
        title = align_special_symbols(title)
        issue_body = align_special_symbols(issue_body)

        issue_templated = issue_github_template.render(
            title=title,
            body=issue_body)

        # кодировка Latin-1 на некоторых задачах приводит к ошибке кодировки в питоне
        issue_templated = issue_templated.encode('utf-8')

        request_result = requests.post(url_gh,
                          data=issue_templated,
                          headers=headers)

        posted_issue = json.loads(request_result.text)

        # занесение в базу данных информацию о том, что данные issues связаны
        linked_issues = Linked_Issues.objects.create_linked_issues(
            issue['issue_id'],              # id issue в редмайне
            posted_issue['id'],             # id issue в гитхабе
            repos_id_gh,                    # id репозитория в гитхабе
            posted_issue['number'])         # номер issue  в репозитории гитхаба

        # ДЕБАГГИНГ
        link_log_rm_post(request_result, issue, linked_issues)

        return request_result

    def post_comment(issue, linked_issues):


        # ------------------------------------------- ОБРАБАТЫВАЕМ ФРАЗУ БОТА ------------------------------------------


        # нет комментария
        if (issue['comment_body'] == ''):
            comment_body = add_bot_phrase(issue, 'comment_body_action')          # добавляем фразу бота
        else:
            comment_body = add_bot_phrase(issue, 'comment_body')    # добавляем фразу бота

        # обработка спец. символов
        comment_body = align_special_symbols(comment_body)


        # ----------------------------------------- ЗАГРУЖАЕМ ДАННЫЕ В ГИТХАБ ------------------------------------------


        comment_templated = comment_github_template.render(body=comment_body)

        # кодировка Latin-1 на некоторых задачах приводит к ошибке кодировки в питоне
        comment_templated = comment_templated.encode('utf-8')

        # добавление issue_id к ссылке
        issue_comments_url_gh = url_gh + '/' + str(linked_issues.issue_num_gh) + '/comments'
        request_result = requests.post(issue_comments_url_gh,
                                       data=comment_templated,
                                       headers=headers)


        # ------------------------------------------- ПРИВЯЗКА КОММЕНТАРИЕВ --------------------------------------------


        #занесение в базу данных информацию о том, что комментарии связаны
        posted_comment = json.loads(request_result.text)
        linked_comments = linked_issues.add_comment(issue['comment_id'],
                                                    posted_comment['id'])

        # ДЕБАГГИНГ
        link_log_rm_comment(request_result, issue, linked_issues, linked_comments)

        return request_result

    def edit_issue(issue, linked_issues):
        # открыть / закрыть issue
        state_gh = "opened"
        if (issue['status_id'] == 12):  # статус issue в редмайне
            state_gh = "closed"

        # дополнительная проверка, что issue связаны
        # (на случай, если изменили не связанный issue)
        if (linked_issues.count() == 0):
            error_text = "ERROR: issue edited in REDMINE, but it's not linked to GITHUB"
            WRITE_LOG('\n' + '='*35 + ' ' + str(datetime.datetime.today()) + ' ' + '='*35 + '\n' +
                      'received webhook from REDMINE: issues | ' + 'action: ' + str(issue['action']) + '\n' +
                      error_text)
            return HttpResponse(error_text, status=404)
        linked_issues = linked_issues[0]


        post_comment(issue, linked_issues) # ОТПРАВЛЯЕМ КОММЕНТАРИЙ В ГИТХАБ


        # ------------------------------------------- ОБРАБАТЫВАЕМ ФРАЗУ БОТА ------------------------------------------

        #title = '[From Redmine (edited)] ' + issue['issue_title']
        title = issue['issue_title']

        # проверяем, если автор issue - бот
        if (chk_if_rm_user_is_a_bot(issue['issue_author_id'])):
            issue_body = del_bot_phrase(issue['issue_body'])    # удаляем фразу бота

        else:
            issue_body = add_bot_phrase(issue, 'issue_body')    # добавляем фразу бота

        # обработка спец. символов
        title = align_special_symbols(title)
        issue_body = align_special_symbols(issue_body)


        # ----------------------------------------- ЗАГРУЖАЕМ ДАННЫЕ В ГИТХАБ ------------------------------------------


        issue_templated = issue_github_template.render(
            title=title,
            body=issue_body,
            state=state_gh)
        # кодировка Latin-1 на некоторых задачах приводит к ошибке кодировки в питоне
        issue_templated = issue_templated.encode('utf-8')

        # добавление issue_id к ссылке
        issue_url_gh = url_gh + '/' + str(linked_issues.issue_num_gh)
        request_result = requests.patch(issue_url_gh,
                                   data=issue_templated,
                                   headers=headers)

        # ДЕБАГГИНГ
        link_log_rm_edit(request_result, issue, linked_issues)

        return request_result


    # привязка комментария на редмайне к гитхабу (да, это костыль)
    # я не хотел делать костыль, но редмайн не посылает внятный ответ на PUT комментария (note)
    def link_comment_to_github(issue, linked_issues):

        # дополнительная проверка, что issue связаны
        # (на случай, если изменили не связанный issue)
        if (linked_issues.count() == 0):
            error_text = "ERROR: issue edited in REDMINE, but it's not linked to GITHUB"
            WRITE_LOG('\n' + '='*35 + ' ' + str(datetime.datetime.today()) + ' ' + '='*35 + '\n' +
                      'received webhook from REDMINE: issues | ' + 'action: ' + str(issue['action']) + '\n' +
                      error_text)
            return HttpResponse(error_text, status=404)
        linked_issues = linked_issues[0]

        # определяем действие (комментарий или измение)
        action = issue['comment_body'].split(' ')[6]

        if(action == 'left'):

            # достаём id комментария в гитхабе
            comment_id_gh_str = issue['comment_body'].split('#issuecomment-')[1]
            comment_id_gh_str = comment_id_gh_str.split(':')[0]
            comment_id_gh = int(comment_id_gh_str)

            # занесение в базу данных информацию о том, что комментарии связаны
            linked_comments = linked_issues.add_comment(issue['comment_id'],
                                                        comment_id_gh)


    # ============================================ ЗАГРУЗКА ISSUE В GITHUB =============================================


    linked_issues = Linked_Issues.objects.get_by_issue_id_rm(issue['issue_id'])
    if (issue['action'] == 'opened'):

        if (chk_if_rm_user_is_a_bot(issue['issue_author_id'])):

            error_text = prevent_cyclic_issue_rm(issue)
            return HttpResponse(error_text, status=200)

        request_result = post_issue(issue)

    elif (issue['action'] == 'updated'):

        if (chk_if_rm_user_is_a_bot(issue['comment_author_id'])):

            # попытка связать комментарий на редмайне с гитхабом
            link_comment_to_github(issue, linked_issues)

            error_text = prevent_cyclic_comment_rm(issue)
            return HttpResponse(error_text, status=200)

        # изменение issue + добавление комментария
        request_result = edit_issue(issue, linked_issues)

    else:
        error_text = 'ERROR: WRONG ACTION'
        WRITE_LOG('\n' + '='*35 + ' ' + str(datetime.datetime.today()) + ' ' + '='*35 + '\n' +
                  'received webhook from REDMINE: issues | ' + 'action: ' + str(issue['action']) + '\n' +
                  error_text)
        return HttpResponse(error_text, status=422)


    return allign_request_result(request_result)
