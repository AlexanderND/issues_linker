import requests
import datetime
from jinja2 import Template
import json
from django.http import HttpResponse                                # ответы серверу (гитхабу)

from issues_linker.quickstart.models import Linked_Projects         # связанные проекты

from issues_linker.my_functions import WRITE_LOG                    # ведение логов
from issues_linker.my_functions import WRITE_LOG_ERR                # ведение логов ошибок
from issues_linker.my_functions import WRITE_LOG_WAR                # ведение логов ошибок
from issues_linker.my_functions import WRITE_LOG_GRN                # ведение логов (многократные действия)
from issues_linker.my_functions import read_file                    # загрузка файла (возвращает строку)

from issues_linker.my_functions import allow_log_project_linking    # разрешить лог связи серверов
from issues_linker.my_functions import detailed_log_project_linking # подробный лог связи серверов
from issues_linker.my_functions import allow_projects_relinking     # повторная связь проектов

from issues_linker.query_data_gh_to_rm import query_data_gh_to_rm   # запрос всех issues и комментариев к ним с гитхаба

# очередь обработки задач
#from issues_linker.quickstart.models import Queue


# TODO: при связи проектов, проверять: а не связани ли они уже
# TODO: при связи проектов, запрашивать: все текущие issues и комментарии к ним
def link_projects(payload):

    payload = json.loads(payload)   # превращаем payload в JSON


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
    # авторизация в redmine по токену (реальный сервер)
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

    # TODO: связь по id
    else:
        #project_id_rm = payload['project_id_rm']
        return 0


    # ========================================== ПОЛУЧЕНИЕ REPOS_ID ГИТХАБА ============================================


    # связь по ссылке
    if (url_gh != ''):
        # удаляем 19 первых символов (https://github.com/)
        repos_url_gh = url_gh[19:]                                      # AlexanderND/test
        api_url_gh = 'https://api.github.com/repos/' + repos_url_gh     # https://api.github.com/repos/AlexanderND/test

        request_result = requests.get(api_url_gh,
                                      headers=headers_gh)

        repos_id_gh = json.loads(request_result.text)['id']

    # TODO: связь по id
    else:
        #repos_id_gh = payload['repos_id_gh']
        return 0


    # ============================================= СОХРАНЕНИЕ ID-ШНИКОВ ===============================================


    def log_link_projects_start():

        if (not allow_log_project_linking):
            return 0

        WRITE_LOG_GRN('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
                      'LINKING PROJECTS IN PROGRESS' + '\n' +
                      'GITHUB       | ---------------------------------------' + '\n' +
                      '             | repos_id:     ' + str(repos_id_gh) + '\n' +
                      '             | repos_url:    ' + url_gh + '\n' +
                      'REDMINE      | ---------------------------------------' + '\n' +
                      '             | project_id:   ' + str(project_id_rm) + '\n' +
                      '             | project_url:  ' + url_rm)

    def log_link_projects_finish():

        if (not allow_log_project_linking):
            return 0

        WRITE_LOG_GRN('FINISHED LINKING PROJECTS' + '\n' +
                      'GITHUB       | ---------------------------------------' + '\n' +
                      '             | repos_id:     ' + str(repos_id_gh) + '\n' +
                      '             | repos_url:    ' + url_gh + '\n' +
                      'REDMINE      | ---------------------------------------' + '\n' +
                      '             | project_id:   ' + str(project_id_rm) + '\n' +
                      '             | project_url:  ' + url_rm + '\n' +
                      '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n')

    # проверка, что проекты уже связаны
    def clear_linked_projects(project_id_rm, repos_id_gh):

        linked_projects = Linked_Projects.objects.get_linked_projects(project_id_rm, repos_id_gh)

        if (len(linked_projects) < 1):
            return 0

        for i in range(len(linked_projects)):
            linked_projects[i].delete()     # удаляем информацию из базы данных


    log_link_projects_start()

    # удаляем информацию о связи из базы данных, если проекты уже связаны
    clear_linked_projects(project_id_rm, repos_id_gh)

    # занесение в базу данных информацию о том, что данные проекты связаны
    linked_projects = Linked_Projects.objects.create_linked_projects(
        project_id_rm,
        repos_id_gh,
        url_rm,
        url_gh)


    # ============================== СОЗДАНИЕ НЕОБХОДИМЫХ ДЛЯ РАБОТЫ LABEL-ОВ В ГИТХАБЕ ================================


    # создание label-ов в гитхабе
    github_label_template = read_file('data/github_label_template.json')
    github_label_template = Template(github_label_template)     # шаблон создания label-ов

    labels_url_gh = api_url_gh + '/labels'


    # загрузка label-ов, необходимых для связи с гитхабом
    github_labels = read_file('data/github_labels.json')
    github_labels = json.loads(github_labels)

    labels = github_labels['labels']

    response_text = 'Projects posted successfully!\n' +\
                    "(or not, I actually don't know)\n" +\
                    "Labels:\n\n"

    # загрузка label-ов в гитхаб
    def log_label_post(label, post_result):

        if (not allow_log_project_linking):
            return 0
        if (not detailed_log_project_linking):
            return 0

        post_result_text = str(post_result.text)

        log_text = '\n' + '-' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '-' * 35 + '\n' +\
                   'POSTing new label to GITHUB:' + '\n' +\
                   'GITHUB       | ---------------------------------------' + '\n' +\
                   '             | repos_id:     ' + str(repos_id_gh) + '\n' +\
                   '             | repos_url:    ' + url_gh + '\n' +\
                   'REDMINE      | ---------------------------------------' + '\n' +\
                   '             | project_id:   ' + str(project_id_rm) + '\n' +\
                   '             | project_url:  ' + url_rm + '\n' +\
                   'LABEL        | ---------------------------------------' + '\n' +\
                   '             | name:         ' + label['name'] + '\n' +\
                   '             | description:  ' + label['description'] + '\n' +\
                   '             | color:        ' + label['color'] + '\n' +\
                   '             | default:      ' + label['default'] + '\n' +\
                   'POST RESULT  | ---------------------------------------' + '\n' +\
                   '             | status:       ' + str(post_result) + '\n' +\
                   '             | text:         ' + post_result_text + '\n'
                   #'-' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '-' * 35 + '\n'

        if (post_result.status_code == 201):
            WRITE_LOG(log_text)

        # скорее всего, label просто уже существует
        elif (post_result.status_code == 422):
            WRITE_LOG_WAR(log_text)

        else:
            WRITE_LOG_ERR(log_text)

    # TODO: исправить постинг label-ов (не приходит description)
    # TODO: исправить постинг label-ов (не приходит default)
    # постим label-ы в гитхаб
    for label in labels:

        # загружаем label-ы
        label_templated = github_label_template.render(
            name=label['name'],
            description=label['description'],
            color=label['color'],
            default=label['default'])

        # кодировка Latin-1 на некоторых задачах приводит к ошибке кодировки в питоне
        label_templated = label_templated.encode('utf-8')

        request_result = requests.post(labels_url_gh,
                                    data=label_templated,
                                    headers=headers_gh)

        log_text = ''
        log_text += label['name'] + '\n'
        log_text += str(request_result) + '\n'
        log_text += str(request_result.text) + '\n'

        # ДЕБАГГИНГ
        log_label_post(label, request_result)

        response_text += log_text


    # =================================== ЗАГРУЗКА ВСЕХ ISSUE ИЗ ГИТХАБА В РЕДМАЙН =====================================


    # запрос issues и комментариев к ним из гитхаба и отправка в редмайн
    query_data_gh_to_rm(linked_projects)

    log_link_projects_finish()

    # TODO: выдавать то же, что выдавалось бы без переопределения метода create
    return HttpResponse(response_text.replace('\n', '<br>'), status=200)    # <br> - новая строка в html


# TODO: добавить в linked_projects поле "last_linking_time" - запрашивать issues старше этого времени (изначально ставим минимальную дату)
def relink_projects(linked_projects):


    # =================================================== ПОДГОТОВКА ===================================================


    # авторизация в redmine по токену (локальный сервер)
    api_key_redmime = read_file('api_keys/api_key_redmime_local.txt')   # загрузка ключа для redmine api
    #api_key_redmime = read_file('api_keys/api_key_redmime.txt')        # загрузка ключа для redmine api
    api_key_redmime = api_key_redmime.replace('\n', '')                 # избавляемся от \n в конце строки

    '''
    # авторизация в redmine по токену (реальный сервер)
    api_key_redmime = read_file('api_keys/api_key_redmime_local.txt')   # загрузка ключа для redmine api
    api_key_redmime = api_key_redmime.replace('\n', '')                 # избавляемся от \n в конце строки
    '''

    # авторизация в гитхабе по токену
    api_key_github = read_file('api_keys/api_key_github.txt')           # загрузка ключа для github api
    api_key_github = api_key_github.replace('\n', '')                   # избавляемся от \n в конце строки


    repos_id_gh = linked_projects.repos_id_gh
    url_gh = linked_projects.url_gh

    project_id_rm = linked_projects.project_id_rm
    url_rm = linked_projects.url_rm


    def log_link_projects_start():

        if (not allow_log_project_linking):
            return 0

        WRITE_LOG_GRN('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
                      'RELINKING PROJECTS IN PROGRESS' + '\n' +
                      'GITHUB       | ---------------------------------------' + '\n' +
                      '             | repos_id:     ' + str(repos_id_gh) + '\n' +
                      '             | repos_url:    ' + url_gh + '\n' +
                      'REDMINE      | ---------------------------------------' + '\n' +
                      '             | project_id:   ' + str(project_id_rm) + '\n' +
                      '             | project_url:  ' + url_rm)

    def log_link_projects_finish():

        if (not allow_log_project_linking):
            return 0

        WRITE_LOG_GRN('FINISHED RELINKING PROJECTS' + '\n' +
                      'GITHUB       | ---------------------------------------' + '\n' +
                      '             | repos_id:     ' + str(repos_id_gh) + '\n' +
                      '             | repos_url:    ' + url_gh + '\n' +
                      'REDMINE      | ---------------------------------------' + '\n' +
                      '             | project_id:   ' + str(project_id_rm) + '\n' +
                      '             | project_url:  ' + url_rm + '\n' +
                      '\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n')

    log_link_projects_start()


    # ================================ ЗАГРУЗКА ВСЕХ НОВЫХ ISSUE ИЗ ГИТХАБА В РЕДМАЙН ==================================


    # запрос issues и комментариев к ним из гитхаба и отправка в редмайн
    query_data_gh_to_rm(linked_projects)

    log_link_projects_finish()

    response_text = "re-linking projects successfully!"

    return HttpResponse(response_text, status=200)    # <br> - новая строка в html
