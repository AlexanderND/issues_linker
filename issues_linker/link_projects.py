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

from issues_linker.query_data_gh_to_rm import query_data_gh_to_rm   # запрос всех issues и комментариев к ним с гитхаба


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


    def log_link_projects_start():

        WRITE_LOG_GRN('\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n' +
                      'LINKING PROJECTS IN PROGRESS' + '\n' +
                      'GITHUB       | ---------------------------------------' + '\n' +
                      '             | repos_id:     ' + str(repos_id_gh) + '\n' +
                      '             | repos_url:    ' + url_gh + '\n' +
                      'REDMINE      | ---------------------------------------' + '\n' +
                      '             | project_id:   ' + str(project_id_rm) + '\n' +
                      '             | project_url:  ' + url_rm)

    def log_link_projects_finish():

        WRITE_LOG_GRN('FINISHED LINKING PROJECTS' + '\n' +
                      'GITHUB       | ---------------------------------------' + '\n' +
                      '             | repos_id:     ' + str(repos_id_gh) + '\n' +
                      '             | repos_url:    ' + url_gh + '\n' +
                      'REDMINE      | ---------------------------------------' + '\n' +
                      '             | project_id:   ' + str(project_id_rm) + '\n' +
                      '             | project_url:  ' + url_rm + '\n' +
                      '\n' + '=' * 35 + ' ' + str(datetime.datetime.today()) + ' ' + '=' * 35 + '\n')


    log_link_projects_start()

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
    '''
    # загрузка label-ов в гитхаб
    def log_label_post(label, post_result):

        post_result_text = str(post_result.text)
        """post_result_text = ''

        # приводим текст ответа в удобный вид
        step = 10
        WRITE_LOG(len(post_result.text))
        for index in range(0, len(post_result.text), step):
            post_result_text += post_result.text[index:]

            # добавляем, чтобы текст находился в правой части консоли
            if ((len(post_result.text) - index - step) > 0):
                post_result_text += '\n             |               '"""

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

        log_text= ''
        log_text += label['name'] + '\n'
        log_text += str(request_result) + '\n'
        log_text += str(request_result.text) + '\n'

        # ДЕБАГГИНГ
        log_label_post(label, request_result)

        response_text += log_text
    '''

    # =================================== ЗАГРУЗКА ВСЕХ ISSUE ИЗ ГИТХАБА В РЕДМАЙН =====================================


    # запрос issues и комментариев к ним из гитхаба и отправка в редмайн
    query_data_gh_to_rm(linked_projects)

    log_link_projects_finish()

    # TODO: выдавать то же, что выдавалось бы без переопределения метода create
    return HttpResponse(response_text.replace('\n', '<br>'), status=200)    # <br> - новая строка в html
