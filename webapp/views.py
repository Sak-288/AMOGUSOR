import django
from django.http import HttpResponse
from django.shortcuts import render


def home(request):
    return render(request, "webapp/home.html")
 

def choose_setting(request):
    if request.method == "POST":
        genderSetting = request.POST.get("gd_setting")
        if genderSetting == "men":
            return redirect('/home_men')
        elif genderSetting == "women":
            return redirect('/home_women')
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