from django.http import HttpResponse
from django.shortcuts import render
from video_hasher import create_video_from_images_optimized


def home(request):
    return render(request, "webapp/home.html")
         