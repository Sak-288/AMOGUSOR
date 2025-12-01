import django
from django.http import HttpResponse
from django.shortcuts import render, redirect
from types import SimpleNamespace
from .image_hasher import hash_image
from .video_hasher import create_video_from_images_optimized
from django.core.files.storage import FileSystemStorage
from .remove_test import remove_everything
import os
from django.core.mail import send_mail 
from django.conf import settings

GLOBAL_FILETYPE = "file"
GLOBAL_RESOLUTION = "32"

def home(request):
    remove_everything()
    noFileMessage = "No file has been selected yet"
    returnDict = {'Specifities':SimpleNamespace(filetype="file", resolution=GLOBAL_RESOLUTION, filename=noFileMessage, isLoader="none")}
    global GLOBAL_FILETYPE
    return render(request, "webapp/home.html", returnDict)
 
def home_video(request):
    remove_everything()
    noFileMessage = "No file has been selected yet"
    returnDict = {'Specifities':SimpleNamespace(filetype="video", resolution=GLOBAL_RESOLUTION, filename=noFileMessage, accFileType="video", isLoader="none")}
    global GLOBAL_FILETYPE
    GLOBAL_FILETYPE = "video"
    return render(request, "webapp/home.html", returnDict)
      
def home_photo(request):
    remove_everything()
    noFileMessage = "No file has been selected yet"
    returnDict = {'Specifities':SimpleNamespace(filetype="photo", resolution=GLOBAL_RESOLUTION, filename=noFileMessage, accFileType="image", isLoader="none")}
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

        chronology_issue = "The file has been downloaded"
        returnDict = {'Specifities':SimpleNamespace(filetype=GLOBAL_FILETYPE, resolution=GLOBAL_RESOLUTION, filename=chronology_issue, isLoader="grid")}
        return render(request, 'webapp/home.html', returnDict)
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
    remove_everything() # Deletes everything previously present in usage directory before new generation
    global GLOBAL_FILETYPE
    global GLOBAL_RESOLUTION
    dir = "media/my_uploads/"
    if GLOBAL_FILETYPE == "photo":
        entry_list = [x for x in os.scandir(dir)]
        hash_image(dir + entry_list[0].name, int(GLOBAL_RESOLUTION))

        accessPath = "webapp/static/webapp/final_image.jpg"
        returnDict = {'Specifities':SimpleNamespace(filetype=GLOBAL_FILETYPE, resolution=GLOBAL_RESOLUTION, doneFilePath=accessPath, isLoader="none")}
    elif GLOBAL_FILETYPE == "video":
        entry_list = [x for x in os.scandir(dir)]
        create_video_from_images_optimized("usage/output.mp4", dir + entry_list[0].name, int(GLOBAL_RESOLUTION), "usage/extracted_frames")
        
        accessPath = "webapp/static/webapp/final_version_with_audio.mp4"
        returnDict = {'Specifities':SimpleNamespace(filetype=GLOBAL_FILETYPE, resolution=GLOBAL_RESOLUTION, doneFilePath=accessPath, isLoader="none")}
    else:
        return redirect('/home')
    return render(request, 'webapp/home.html', returnDict)

def choose_file(request):
    if request.method == "POST":
        uploaded_file = request.FILES.get("file")
        if uploaded_file:
            destination_path = "media/my_uploads/"

            for filepath in os.scandir(destination_path):
                os.remove(filepath)
            
            # Django Magic File Storing
            fs = FileSystemStorage()
            filename = fs.save('my_uploads/' + uploaded_file.name, uploaded_file) 

            returnDict = {'Specifities':SimpleNamespace(filetype=GLOBAL_FILETYPE, resolution=GLOBAL_RESOLUTION, filename=uploaded_file.name, isLoader="none")}
        else:
            noFileMessage = "Error in file choosing"
            returnDict = {'Specifities':SimpleNamespace(filetype=GLOBAL_FILETYPE, resolution=GLOBAL_RESOLUTION, filename=noFileMessage, isLoader="none")}
    return render(request, 'webapp/home.html', returnDict)