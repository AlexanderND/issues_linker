import requests
import datetime
from jinja2 import Template
import json
from django.http import HttpResponse                                # ответы серверу (редмайну)

from issues_linker.quickstart.models import Linked_Projects         # связанные проекты
from issues_linker.quickstart.models import Linked_Issues           # связанные issues
from issues_linker.quickstart.models import Linked_Comments         # связанные комментарии

from issues_linker.my_functions import WRITE_LOG                    # ведение логов
from issues_linker.my_functions import WRITE_LOG_WAR                # ведение логов (предупреждения)
from issues_linker.my_functions import align_special_symbols        # обработка спец. символов (\ -> \\)
from issues_linker.my_functions import read_file                    # загрузка файла (возвращает строку)

#from issues_linker.my_functions import repos_id_gh                  # id репозитория в гитхабе
from issues_linker.my_functions import make_gh_repos_url            # ссылка на гитхаб

from issues_linker.my_functions import chk_if_rm_user_is_our_bot    # проверка на бота (предотвращение
                                                                    # зацикливания: RM -> S -> GH -> ...)
from issues_linker.my_functions import log_issue_post_rm            # лог связи issues (создание)
from issues_linker.my_functions import log_issue_edit_rm            # лог связи issues (изменение)
from issues_linker.my_functions import log_comment_rm               # лог связи issues (комментарий)
from issues_linker.my_functions import prevent_cyclic_issue_rm      # предотвращение зацикливания issue
from issues_linker.my_functions import prevent_cyclic_comment_rm    # предотвращение зацикливания комментариев

from issues_linker.my_functions import del_bot_phrase               # удаление фразы бота

from issues_linker.my_functions import allign_request_result        # создание корректного ответа серверу

from issues_linker.my_functions import match_tracker_to_gh          # сопоставление label-ов
from issues_linker.my_functions import match_status_to_gh           # сопоставление label-ов
from issues_linker.my_functions import match_priority_to_gh         # сопоставление label-ов

from issues_linker.my_functions import tracker_ids_rm               # ids трекеров задачи в редмайне
from issues_linker.my_functions import status_ids_rm                # ids статусов задачи в редмайне
from issues_linker.my_functions import priority_ids_rm              # ids приоритетов задачи в редмайне
from issues_linker.my_functions import url_rm                       # ссылка на сервер редмайна


def process_payload_from_rm(payload):
    payload = payload['payload']    # достаём содержимое payload. payload payload. payload? payload!


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
        payload_parsed['tracker_id'] = payload['issue']['tracker']['id']
        payload_parsed['status_id'] = payload['issue']['status']['id']
        payload_parsed['priority_id'] = payload['issue']['priority']['id']

        # идентификаторы (для связи и логов)
        payload_parsed['issue_id'] = payload['issue']['id']
        payload_parsed['project_id'] = payload['issue']['project']['id']

        # ссылка на issue (для фразы бота и логов)
        payload_parsed['issue_url'] = payload['url']

        return payload_parsed

    issue = parse_payload(payload)

    # авторизация в гитхабе по токену
    api_key_github = read_file('api_keys/api_key_github.txt')   # загрузка ключа для github api
    api_key_github = api_key_github.replace('\n', '')  # избавляемся от \n в конце строки

    # загрузка issue template из файла
    issue_github_template = read_file('parsed_data_templates/issue_github_template.json')
    issue_github_template = Template(issue_github_template)  # шаблон для каждого issue

    # загрузка comment template из файла
    comment_github_template = read_file('parsed_data_templates/comment_github_template.json')
    comment_github_template = Template(comment_github_template)  # шаблон для каждого issue

    # заголовки авторизации и приложения, при отправке запросов на гитхаб
    headers = {'Authorization': 'token ' + api_key_github,
               'Content-Type': 'application/json'}


    # ============================================ ВСПОМОГАТЕЛЬНЫЕ КОМАНДЫ =============================================


    # issue_body
    # comment_body
    # comment_body_action
    # issue_label
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
                      "\nAlternatively, add logic to process '" + to + "' action correctly.\n")

            return None

    # обновление linked_issues в базе данных сервера (tracker_id, status_id, priority_id)
    def update_linked_issues(linked_issues, issue):

        linked_issues.tracker_id_rm = issue['tracker_id']
        linked_issues.priority_id_rm = issue['priority_id']

        # если rejected
        if (issue['status_id'] == status_ids_rm[4]):
            linked_issues.is_opened = False
            linked_issues.status_id_rm = issue['priority_id']

        # если closed
        elif (issue['status_id'] == status_ids_rm[5]):
            linked_issues.is_opened = False

        # иначе - открываем
        else:
            linked_issues.is_opened = True
            linked_issues.status_id_rm = issue['priority_id']

        linked_issues.save()


    # типичные ошибки на этапе проверки: не связаны проекты, задачи, комментарии, неизвестное действие и т.п.
    def PREPARATION_ERR(error_text):

        # добавляем, чтобы в начале получилось: 'PREPARATION ERROR'
        error_text = 'PREPARATION ' + error_text

        WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
                  'received webhook from REDMINE: issues | ' + 'action: ' + str(issue['action']) + '\n' +
                  error_text)

        return HttpResponse(error_text, status=404)

    # логическая ошибка: неизвестное действие, неправильные label-ы в гитхабе и т.п.
    def LOGICAL_ERR(error_text):

        # добавляем, чтобы в начале получилось: 'LOGICAL ERROR'
        error_text = 'LOGICAL ' + error_text

        WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
                  'received webhook from REDMINE: issues | ' + 'action: ' + str(issue['action']) + '\n' +
                  error_text)

        return HttpResponse(error_text, status=422)


    # ============================================= КОМАНДЫ ДЛЯ ЗАГРУЗКИ ===============================================


    def post_issue(linked_projects, issue):


        # ----------------------------------------------- ПОДГОТОВКА -----------------------------------------------


        # дополнительная проверка, что проекты связаны
        if (linked_projects.count() == 0):

            error_text = "ERROR: process_payload_from_rm.post_issue\n" +\
                         "issue " + str(issue['action']) + " in REDMINE, but the project is not linked to GITHUB"

            return PREPARATION_ERR(error_text)

        linked_projects = linked_projects[0]

        repos_id_gh = linked_projects.repos_id_gh
        url_gh = make_gh_repos_url(repos_id_gh)


        # ------------------------------------------ ОБРАБОТКА ФРАЗЫ БОТА -----------------------------------------


        #title = '[From Redmine] ' + issue['issue_title']
        title = issue['issue_title']
        issue_body = add_bot_phrase(issue, 'issue_body')    # добавляем фразу бота

        # обработка спец. символов
        title = align_special_symbols(title)
        issue_body = align_special_symbols(issue_body)


        # --------------------------------------- ЗАГРУЗКА ДАННЫХ В ГИТХАБ ----------------------------------------


        # добавление label-ов
        tracker = match_tracker_to_gh(issue['tracker_id'])
        status = match_status_to_gh(issue['status_id'])
        priority = match_priority_to_gh(issue['priority_id'])

        issue_templated = issue_github_template.render(
            title=title,
            body=issue_body,
            priority=priority,
            status=status,
            tracker=tracker)

        # кодировка Latin-1 на некоторых задачах приводит к ошибке кодировки в питоне
        issue_templated = issue_templated.encode('utf-8')

        request_result = requests.post(url_gh,
                                       data=issue_templated,
                                       headers=headers)


        # ------------------------------------------ СОХРАНЕНИЕ ДАННЫХ --------------------------------------------


        posted_issue = json.loads(request_result.text)

        # занесение в базу данных информацию о том, что данные issues связаны
        linked_issues = Linked_Issues.objects.create_linked_issues(
            issue['issue_id'],              # id issue в редмайне
            posted_issue['id'],             # id issue в гитхабе
            repos_id_gh,                    # id репозитория в гитхабе
            posted_issue['number'],         # номер issue  в репозитории гитхаба
            issue['tracker_id'],            # id трекера в редмайне
            issue['status_id'],             # id статуса в редмайне
            issue['priority_id'])           # id приоритета в редмайне

        # добавляем linked_issues в linked_projects
        linked_projects.add_linked_issues(linked_issues)


        # ДЕБАГГИНГ
        log_issue_post_rm(request_result, issue, linked_issues)

        return request_result

    # загрузка комментария. нет необходимости в подготовке, так как запускается из edit_issue
    # (redmine не различает оставление комментария и изменение issue)
    def post_comment(linked_issues, issue, url_gh):


        # ------------------------------------------ ОБРАБОТКА ФРАЗЫ БОТА -----------------------------------------


        # нет комментария
        if (issue['comment_body'] == ''):
            comment_body = add_bot_phrase(issue, 'comment_body_action')     # добавляем фразу бота
        else:
            comment_body = add_bot_phrase(issue, 'comment_body')            # добавляем фразу бота

        # обработка спец. символов
        comment_body = align_special_symbols(comment_body)


        # --------------------------------------- ЗАГРУЗКА ДАННЫХ В ГИТХАБ ----------------------------------------


        comment_templated = comment_github_template.render(body=comment_body)

        # кодировка Latin-1 на некоторых задачах приводит к ошибке кодировки в питоне
        comment_templated = comment_templated.encode('utf-8')

        # добавление issue_id к ссылке
        issue_comments_url_gh = url_gh + '/' + str(linked_issues.issue_num_gh) + '/comments'
        request_result = requests.post(issue_comments_url_gh,
                                       data=comment_templated,
                                       headers=headers)


        # ------------------------------------------ СОХРАНЕНИЕ ДАННЫХ --------------------------------------------


        #занесение в базу данных информации о том, что комментарии связаны
        posted_comment = json.loads(request_result.text)
        linked_comments = linked_issues.add_comment(issue['comment_id'],
                                                    posted_comment['id'])

        # ДЕБАГГИНГ
        log_comment_rm(request_result, issue, linked_issues, linked_comments)

        return request_result

    # TODO: rejected в редмайне -> удаление в гитхабе?
    def edit_issue(linked_projects, issue):


        # ----------------------------------------------- ПОДГОТОВКА -----------------------------------------------


        # дополнительная проверка, что проекты связаны
        if (linked_projects.count() == 0):

            error_text = "ERROR: process_payload_from_rm.edit_issue\n" +\
                         "issue " + str(issue['action']) + " in REDMINE, but the project is not linked to GITHUB"

            return PREPARATION_ERR(error_text)

        linked_projects = linked_projects[0]

        repos_id_gh = linked_projects.repos_id_gh
        url_gh = make_gh_repos_url(repos_id_gh)

        linked_issues = linked_projects.get_issue_by_id_rm(issue['issue_id'])

        # дополнительная проверка, что issue связаны
        if (linked_issues.count() == 0):

            error_text = "ERROR: process_payload_from_rm.edit_issue\n" +\
                         "issue " + str(issue['action']) + " in REDMINE, but it's not linked to GITHUB"

            return PREPARATION_ERR(error_text)

        linked_issues = linked_issues[0]

        # добавление label-ов
        state_gh = "opened"  # открыть / закрыть issue
        if (issue['tracker_id'] != linked_issues.tracker_id_rm):
            tracker = match_tracker_to_gh(issue['tracker_id'])
        else:
            tracker = match_tracker_to_gh(linked_issues.tracker_id_rm)

        if (issue['status_id'] != linked_issues.status_id_rm):
            status = match_status_to_gh(issue['status_id'])

            if (status == 'Status: closed'):
                status = match_status_to_gh(linked_issues.status_id_rm)  # не меняем статус (нет label-а closed)
                state_gh = 'closed'

            elif (status == 'Status: rejected'):
                state_gh = 'closed'
        else:
            status = match_status_to_gh(linked_issues.status_id_rm)

        if (issue['priority_id'] != linked_issues.priority_id_rm):
            priority = match_priority_to_gh(issue['priority_id'])
        else:
            priority = match_priority_to_gh(linked_issues.priority_id_rm)

        post_comment(linked_issues, issue, url_gh)     # ОТПРАВЛЯЕМ КОММЕНТАРИЙ В ГИТХАБ


        # ----------------------------------------- ОБРАБОТКА ФРАЗЫ БОТА -------------------------------------------


        #title = '[From Redmine (edited)] ' + issue['issue_title']
        title = issue['issue_title']

        # проверяем, если автор issue - бот
        if (chk_if_rm_user_is_our_bot(issue['issue_author_id'])):
            issue_body = del_bot_phrase(issue['issue_body'])    # удаляем фразу бота

        else:
            issue_body = add_bot_phrase(issue, 'issue_body')    # добавляем фразу бота

        # обработка спец. символов
        title = align_special_symbols(title)
        issue_body = align_special_symbols(issue_body)


        # ---------------------------------------- ЗАГРУЗКА ДАННЫХ В ГИТХАБ ----------------------------------------


        issue_templated = issue_github_template.render(
            title=title,
            body=issue_body,
            state=state_gh,
            priority=priority,
            status=status,
            tracker=tracker)
        # кодировка Latin-1 на некоторых задачах приводит к ошибке кодировки в питоне
        issue_templated = issue_templated.encode('utf-8')

        # добавление issue_id к ссылке
        issue_url_gh = url_gh + '/' + str(linked_issues.issue_num_gh)
        request_result = requests.patch(issue_url_gh,
                                   data=issue_templated,
                                   headers=headers)


        # ------------------------------------------ СОХРАНЕНИЕ ДАННЫХ --------------------------------------------


        # обновляем информацию в таблице
        update_linked_issues(linked_issues,
                             issue)

        # ДЕБАГГИНГ
        log_issue_edit_rm(request_result, issue, linked_issues)

        return request_result


    # привязка комментария на редмайне к гитхабу (да, это костыль)
    # пришлось привязать к id комментария в фразе бота на редмайне (редмайн не посылает внятный ответ на PUT запрос)
    def link_comment_to_github(linked_projects, issue):


        # ----------------------------------------------- ПОДГОТОВКА -----------------------------------------------


        # дополнительная проверка, что проекты связаны
        if (linked_projects.count() == 0):

            error_text = "ERROR: process_payload_from_rm.link_comment_to_github\n" +\
                         "tried to link comment from REDMINE to GITHUB, but the project is not linked to GITHUB"

            return PREPARATION_ERR(error_text)

        linked_projects = linked_projects[0]

        linked_issues = linked_projects.get_issue_by_id_rm(issue['issue_id'])

        # дополнительная проверка, что issue связаны
        if (linked_issues.count() == 0):

            error_text = "ERROR: process_payload_from_rm.link_comment_to_github\n" +\
                         "tried to link comment from REDMINE to GITHUB, but the issue is not linked to GITHUB"

            return PREPARATION_ERR(error_text)

        linked_issues = linked_issues[0]

        # определяем действие (определяем, нужно ли привязывать комментарий к гитхабу -
        # комментарий от бота может оказаться сообщением о действии пользователя на гитхабе
        action = issue['comment_body'].split(' ')[6]
        if(action == 'left'):

            # достаём id комментария в гитхабе
            comment_id_gh_str = issue['comment_body'].split('#issuecomment-')[1]
            comment_id_gh_str = comment_id_gh_str.split(' ')[0]
            comment_id_gh = int(comment_id_gh_str)

            # занесение в базу данных информацию о том, что комментарии связаны
            linked_comments = linked_issues.add_comment(issue['comment_id'],
                                                        comment_id_gh)

            responce_text = "Comment linked to GITHUB successfully."
            return HttpResponse(responce_text, status=201)

        else:

            error_text = prevent_cyclic_comment_rm(issue)
            return HttpResponse(error_text, status=200)


    # ============================================ ЗАГРУЗКА ISSUE В GITHUB =============================================


    block_action_opened = True  # запрет копирования задач: RM -> GH

    linked_projects = Linked_Projects.objects.get_by_project_id_rm(issue['project_id'])
    if (issue['action'] == 'opened'):

        if (chk_if_rm_user_is_our_bot(issue['issue_author_id'])):

            error_text = prevent_cyclic_issue_rm(issue)
            return HttpResponse(error_text, status=200)

        if (block_action_opened):

            error_text = "WARNING: process_payload_from_rm\n" + \
                         "PROHIBITED ACTION"

            WRITE_LOG('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
                      'received webhook from REDMINE: issues | ' + 'action: ' + str(issue['action']) + '\n' +
                      error_text)

            return HttpResponse(error_text, status=403)

        request_result = post_issue(linked_projects, issue)

    elif (issue['action'] == 'updated'):

        if (chk_if_rm_user_is_our_bot(issue['comment_author_id'])):

            # попытка связать комментарий на редмайне с гитхабом
            return link_comment_to_github(linked_projects, issue)

        # изменение issue + добавление комментария
        request_result = edit_issue(linked_projects, issue)

    else:

        error_text = "ERROR: process_payload_from_rm.link_comment_to_github\n" + \
                     "WRONG ACTION"

        return LOGICAL_ERR(error_text)


    return allign_request_result(request_result)
