"""
URL configuration for ceibs_management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('elevated/', admin.site.urls),
    path('account/', include('account.urls')),
    path('students/', include('students.urls')),
    path('finance/', include('finance.urls')),
    path('events/', include('events.urls')),
    path('marketing/', include('marketing.urls')),
    path('', include('elevated.urls')),
    path('student_grading/', include('student_grading.urls')),
    path('alumni/', include('alumni.urls')),
    path('academic_program/', include('academic_program.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)


