from django.http import HttpResponse
from video_hasher import create_video_from_images_optimized


def home(request):
    create_video_from_images_optimized('final_version.mp4', 'video.mp4')
    return HttpResponse("hello, you're at home")