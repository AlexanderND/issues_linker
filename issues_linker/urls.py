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
from issues_linker.quickstart import views

router = routers.DefaultRouter()

'''# testing
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)'''

router.register(r'payloads_from_github', views.Payload_From_GH_ViewSet)
router.register(r'comment_payloads_from_github', views.Comment_Payload_From_GH_ViewSet)
router.register(r'payloads_from_redmine', views.Payload_From_RM_ViewSet)
router.register(r'linked_issues', views.Linked_Issues_ViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
