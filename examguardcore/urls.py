"""
URL configuration for examguardcore project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/lecturer/', include('lecturer_portal.urls', namespace='lecturer_portal_api')),
    path('lecturer/', include('lecturer_portal.page_urls', namespace='lecturer_portal')),
    path('api/student/', include('student_portal.urls', namespace='student_portal_api')),
    path('student/', include('student_portal.page_urls', namespace='student_portal_pages')),
]
