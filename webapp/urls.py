from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('home/', views.home, name="home"),
    path('choose_setting/', views.choose_setting, name='choose_setting'),
    path('choose_resolution/', views.choose_resolution, name='choose_resolution'),
    path('contact/', views.contact, name='contact'),
    path('home_video/', views.home_video, name='home_video'),
    path('home_photo/', views.home_photo, name='home_photo'),
    path('generate/', views.generate, name='generate'),
    path('choose_file/', views.choose_file, name='choose_file'),
]