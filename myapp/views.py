import csv
import base64
from datetime import datetime, timedelta
from django.contrib import messages
from django.contrib.auth import (authenticate, login, logout,update_session_auth_hash)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User , AbstractUser
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import F, Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import CustomUser
from .forms import (CustomSetPasswordForm,SignUpForm)
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.views import View
from django.core.files.storage import default_storage
from PIL import Image
from io import BytesIO
from django.http import JsonResponse
from .models import ChatHistory
from django.contrib.auth.decorators import login_required


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.first_name = form.cleaned_data.get('first_name')
            user.last_name = form.cleaned_data.get('last_name')
            user.phone = form.cleaned_data.get('phone')
            user.address = form.cleaned_data.get('address')
            user.save()
            login(request, user)
            messages.success(request, 'Your account has been created successfully!',extra_tags='success')
            return redirect('signin')
    else:
        form = SignUpForm()

    return render(request, 'Sign_up.html',{'form': form})


def signin(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}.")
                if remember_me:
                    request.session.set_expiry(timedelta(days=7).total_seconds())
                else:
                    request.session.set_expiry(0)

                return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()

    context = {'form': form}
    return render(request, 'Sign_in.html', context)

#######################this function is used for signout
@login_required
def logout_view(request):
    logout(request)
    return redirect('signin')



@login_required
def chat_view(request):
    if request.method == "POST":
        user_query = request.POST.get("message", "")
        
        # Call the chatbot API
        response = requests.post(
            "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill",
            headers={"Content-Type": "application/json"},
            json={"inputs": user_query},
        ).json()

        # Get bot response
        bot_reply = response.get("generated_text", "Sorry, I didn't understand that.")

        # Save the conversation in the database
        chat_history = ChatHistory.objects.create(
            user=request.user,
            query=user_query,
            response=bot_reply
        )

        # Return response as JSON
        return JsonResponse({"query": user_query, "response": bot_reply})

    # Render the chat page for GET requests
    return render(request, "home.html")



@login_required
def QueryHistory(request):
    user_history = ChatHistory.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'query_history.html', {'history': user_history})


def FAQ(request):
    pass

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

@login_required
def ExportPDF(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="chat_history.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    y = 750  # Y-coordinate for the starting position on the PDF

    chats = ChatHistory.objects.filter(user=request.user).order_by('timestamp')
    p.drawString(100, 800, f"Chat History for {request.user.username}")

    for chat in chats:
        p.drawString(100, y, f"Date: {chat.timestamp}")
        y -= 20
        p.drawString(100, y, f"You: {chat.query}")
        y -= 20
        p.drawString(100, y, f"Bot: {chat.response}")
        y -= 40
        if y < 50:  # Move to a new page if nearing the end
            p.showPage()
            y = 750

    p.save()
    return response


@login_required
def ExportCSV(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="chat_history.csv"'

    writer = csv.writer(response)
    writer.writerow(['User', 'Query', 'Response', 'Timestamp'])

    for chat in ChatHistory.objects.filter(user=request.user).order_by('timestamp'):
        writer.writerow([chat.user.username, chat.query, chat.response, chat.timestamp])

    return response



