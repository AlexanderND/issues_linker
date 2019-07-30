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

    # TODO: выдавать то же, что выдавалось бы без переопределения метода create
    return HttpResponse('Projects posted successfully!', status=200)
