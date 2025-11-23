import django
from django.http import HttpResponse
from django.shortcuts import render, redirect
from types import SimpleNamespace
from .image_hasher import hash_image
from .video_hasher import create_video_from_images_optimized

GLOBAL_FILETYPE = "file"
GLOBAL_RESOLUTION = "32"

def home(request):
    returnDict = {'Specifities':SimpleNamespace(filetype="file", resolution=GLOBAL_RESOLUTION)}
    global GLOBAL_FILETYPE
    GLOBAL_FILETYPE = "file"
    return render(request, "webapp/home.html", returnDict)
 
def home_video(request):
    returnDict = {'Specifities':SimpleNamespace(filetype="video", resolution=GLOBAL_RESOLUTION)}
    global GLOBAL_FILETYPE
    GLOBAL_FILETYPE = "video"
    return render(request, "webapp/home.html", returnDict)

def home_photo(request):
    returnDict = {'Specifities':SimpleNamespace(filetype="photo", resolution=GLOBAL_RESOLUTION)}
    global GLOBAL_FILETYPE
    GLOBAL_FILETYPE = "photo"
    return render(request, "webapp/home.html", returnDict)

def choose_setting(request):
    if request.method == "POST":
        genderSetting = request.POST.get("gd_setting")
        if genderSetting == "photo":
            return redirect('/home_photo')
        elif genderSetting == "video":
            return redirect('/home_video')
        else:
            return redirect('/home')

def choose_resolution(request):
    if request.method == "POST":
        genderSetting = request.POST.get("gd_setting")
        global GLOBAL_RESOLUTION
        if genderSetting == "8":
            GLOBAL_RESOLUTION = "8"
        elif genderSetting == "12":
            GLOBAL_RESOLUTION = "12"
        elif genderSetting == "16":
            GLOBAL_RESOLUTION = "16"
        elif genderSetting == "32":
            GLOBAL_RESOLUTION = "32"
        elif genderSetting == "48":
            GLOBAL_RESOLUTION = "48"
        elif genderSetting == "64":
            GLOBAL_RESOLUTION = "64"
        else:
            GLOBAL_RESOLUTION = "32"

        if GLOBAL_FILETYPE == "file":
            return redirect('/home')
        elif GLOBAL_FILETYPE == "photo":
            return redirect('/home_photo')
        elif GLOBAL_FILETYPE == "video":
            return redirect('/home_video')
    else:
        return redirect('/home')


def contact(request):
    if request.method == "POST":
        name = request.POST['name']
        email = request.POST['email']
        subject = request.POST['subject']

        message = f"""Name  {name} 
    Email : <{email}> :\n\n{subject}"""

        send_mail(
            subject=f"Smash or Pass - Message de {name}",
            message=message,
            from_email=settings.EMAIL_HOST_USER,  # authenticated sender
            recipient_list=[settings.EMAIL_HOST_USER],  # send to yourself
            fail_silently=False,
        )

        return redirect('/home')

    return render(request, 'webapp/contact.html')

def generate(request):
    global GLOBAL_FILETYPE
    global GLOBAL_RESOLUTION
    if GLOBAL_FILETYPE == "photo":
        hash_image("input.jpg", int(GLOBAL_RESOLUTION))
    elif GLOBAL_FILETYPE == "video":
        create_video_from_images_optimized("output.mp4", "input.mp4", int(GLOBAL_RESOLUTION), "extracted_frames")
    else:
        return redirect('/home')
    return redirect('/home')