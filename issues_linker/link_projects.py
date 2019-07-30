import requests
import datetime
from jinja2 import Template
import json
from django.http import HttpResponse                                # ответы серверу (гитхабу)

from issues_linker.quickstart.models import Linked_Projects         # связанные проекты
from issues_linker.quickstart.models import Linked_Issues           # связанные issues

from issues_linker.my_functions import WRITE_LOG                    # ведение логов
from issues_linker.my_functions import align_special_symbols        # обработка спец. символов (\ -> \\)
from issues_linker.my_functions import read_file                    # загрузка файла (возвращает строку)

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

from issues_linker.my_functions import make_gh_repos_url            # ссылка на гитхаб


# TODO: при связи проектов, проверять: а не связани ли они уже
# TODO: при связи проектов, запрашивать: все текущие issues и комментарии к ним
def link_projects(payload):


    # =================================================== ПОДГОТОВКА ===================================================


    # достаём id из payload-а
    #project_id_rm = payload['project_id_rm']
    #repos_id_gh = payload['repos_id_gh']

    # достаём ссылки из payload-а
    url_rm = payload['url_rm']
    url_gh = payload['url_gh']

    # авторизация в redmine по токену (локальный сервер)
    api_key_redmime = read_file('api_keys/api_key_redmime_local.txt')   # загрузка ключа для redmine api
    #api_key_redmime = read_file('api_keys/api_key_redmime.txt')        # загрузка ключа для redmine api
    api_key_redmime = api_key_redmime.replace('\n', '')                 # избавляемся от \n в конце строки

    '''
    # авторизация в redmine по токену (реальный сервер
    api_key_redmime = read_file('api_keys/api_key_redmime_local.txt')   # загрузка ключа для redmine api
    api_key_redmime = api_key_redmime.replace('\n', '')                 # избавляемся от \n в конце строки
    '''

    # авторизация в гитхабе по токену
    api_key_github = read_file('api_keys/api_key_github.txt')           # загрузка ключа для github api
    api_key_github = api_key_github.replace('\n', '')                   # избавляемся от \n в конце строки

    # заголовки авторизации и приложения, при отправке запросов на редмайн
    headers_rm = {'X-Redmine-API-Key': api_key_redmime,
                  'Content-Type': 'application/json'}

    # заголовки авторизации и приложения, при отправке запросов на гитхаб
    headers_gh = {'Authorization': 'token ' + api_key_github,
                  'Content-Type': 'application/json'}


    # ========================================= ПОЛУЧЕНИЕ PROJECT_ID РЕДМАЙНА ==========================================


    # связь по ссылке
    if (url_rm != ''):
        # для удобства, выводим как json
        api_url_rm = url_rm + '.json'
        request_result = requests.get(api_url_rm,
                                      headers=headers_gh)

        project_id_rm = json.loads(request_result.text)['project']['id']

    # связь по id
    #else:
    #    project_id_rm = payload['project_id_rm']


    # ========================================== ПОЛУЧЕНИЕ REPOS_ID ГИТХАБА ============================================


    # связь по ссылке
    if (url_gh != ''):
        # удаляем 19 первых символов (https://github.com/)
        repos_url_gh = url_gh[19:]                                      # AlexanderND/test
        api_url_gh = 'https://api.github.com/repos/' + repos_url_gh     # https://api.github.com/repos/AlexanderND/test

        request_result = requests.get(api_url_gh,
                                      headers=headers_gh)

        repos_id_gh = json.loads(request_result.text)['id']

    # связь по id
    #else:
    #    repos_id_gh = payload['repos_id_gh']


    # ============================================= СОХРАНЕНИЕ ID-ШНИКОВ ===============================================


    # занесение в базу данных информацию о том, что данные проекты связаны
    linked_projects = Linked_Projects.objects.create_linked_projects(
        project_id_rm,
        repos_id_gh,
        url_rm,
        url_gh)


    # ============================== СОЗДАНИЕ НЕОБХОДИМЫХ ДЛЯ РАБОТЫ LABEL-ОВ В ГИТХАБЕ ================================


    # создание label-ов в гитхабе
    create_label_github_template = read_file('parsed_data_templates/create_label_github_template.json')
    create_label_github_template = Template(create_label_github_template)  # шаблон создания label-ов

    labels_url_gh = api_url_gh + '/labels'

    # label-ы, необходимые для работы связи
    # (да, немного некрасиво выглядит)
    labels = [{}, {}, {}, {}, {}, {}, {}, {}, {}, {}]

    labels[0]['name'] = 'Priority: low'
    labels[0]['description'] = 'Low priority issue'
    labels[0]['color'] = '#ffe99c'

    labels[1]['name'] = 'Priority: normal'
    labels[1]['description'] = "Most issues should have 'normal' priority"
    labels[1]['color'] = '#ffdb5e'

    labels[2]['name'] = 'Priority: urgent'
    labels[2]['description'] = 'Urgent issue'
    labels[2]['color'] = '#ffc600'

    labels[3]['name'] = 'Status: feedback'
    labels[3]['description'] = 'We are awaiting your feedback on the issue'
    labels[3]['color'] = '#85ffb0'

    labels[4]['name'] = 'Status: new'
    labels[4]['description'] = 'Default status for new issues'
    labels[4]['color'] = '#2b57ff'

    labels[5]['name'] = 'Status: rejected'
    labels[5]['description'] = 'Issue rejected'
    labels[5]['color'] = '#a80000'

    labels[6]['name'] = 'Status: verification'
    labels[6]['description'] = 'We are verifying, that the issue has been resolved'
    labels[6]['color'] = '#c9ffdc'

    labels[7]['name'] = 'Status: working'
    labels[7]['description'] = 'We are working on it. Please, be patient!'
    labels[7]['color'] = '#38ff7e'

    labels[8]['name'] = 'Tracker: bug'
    labels[8]['description'] = "Something isn't working"
    labels[8]['color'] = '#e00000'

    labels[9]['name'] = 'Tracker: task'
    labels[9]['description'] = 'Suggestions or the like'
    labels[9]['color'] = '#2b57ff'

    response_text = 'Projects posted successfully!\n' +\
                    "(or not, I actually don't know)\n"+\
                    "Labels:\n\n"

    # TODO: исправить постинг label-ов
    # постим label-ы в гитхаб
    for label in labels:

        label_templated = create_label_github_template.render(
            name=label['name'],
            description=label['description'],
            color=label['color'])

        # кодировка Latin-1 на некоторых задачах приводит к ошибке кодировки в питоне
        label_templated = label_templated.encode('utf-8')

        request_result = requests.post(labels_url_gh,
                                       data=label_templated,
                                       headers=headers_gh)
        response_text += label['name'] + '\n'
        response_text += str(request_result) + '\n'
        response_text += str(request_result.text) + '\n'


    WRITE_LOG(response_text)
    # TODO: выдавать то же, что выдавалось бы без переопределения метода create
    return HttpResponse(response_text, status=200)
