"""issues_linker URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import include, path
from rest_framework import routers

# мои модели (хранение на сервере)
#from issues_linker.quickstart.views import Comment_Payload_From_GH_ViewSet
from issues_linker.quickstart.views import Payload_From_GH_ViewSet, Payload_From_RM_ViewSet

# мои модели (связь)
from issues_linker.quickstart.views import Linked_Projects_ViewSet, Linked_Issues_ViewSet, Linked_Comments_ViewSet

# мои модели (очередь обработки задач)
from issues_linker.quickstart.views import Tasks_In_Queue_ViewSet

# форма связи проектов
from issues_linker.quickstart.views import Linked_Projects_List, Linked_Project_Detail

router = routers.DefaultRouter()

'''# testing
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)'''


# ХРАНЕНИЕ НА СЕРВЕРЕ
router.register(r'payloads_from_github', Payload_From_GH_ViewSet)
#router.register(r'comment_payloads_from_github', Comment_Payload_From_GH_ViewSet)
router.register(r'payloads_from_redmine', Payload_From_RM_ViewSet)


# СВЯЗЬ
router.register(r'linked_projects', Linked_Projects_ViewSet)
router.register(r'linked_issues', Linked_Issues_ViewSet)
router.register(r'linked_comments', Linked_Comments_ViewSet)


# ОЧЕРЕДЬ ОБРАБОТКИ ЗАДАЧ
router.register(r'queue_task', Tasks_In_Queue_ViewSet)


# ФОРМА СВЯЗИ ПРОЕКТОВ
#router.register(r'linked_projects_list', Linked_Projects_List)
#router.register(r'linked_project_detail', Linked_Project_Detail)


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
