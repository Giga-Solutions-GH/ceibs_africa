from django.urls import path

from elevated import views

app_name = 'elevated'

urlpatterns = [
    path('', views.home, name='home'),
]