import csv
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth import (authenticate, login, logout)
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from .forms import SignUpForm
from .models import ChatHistory, ActionLog
import requests
from django.contrib.auth.decorators import login_required, user_passes_test
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

HUGGING_FACE_API_KEY = "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"

def log_action(user, action_type, details=None):
    ActionLog.objects.create(user=user, action_type=action_type, details=details)

@login_required
def view_own_logs(request):
    logs = ActionLog.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'view_own_logs.html', {'logs': logs})

def staff_or_admin_required(view_func):
    return user_passes_test(lambda u: u.is_staff)(view_func)

@staff_or_admin_required
def view_all_logs(request):
    logs = ActionLog.objects.all().order_by('-timestamp')
    return render(request, 'view_logs.html', {'logs': logs})


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.info(request, f"You are now signed up and logged in as {user.username}.")
            log_action(user, 'SIGNUP_SUCCESS', f"User signed up and logged in.")
            return redirect('home')
        else:
            messages.error(request, 'There was an error during sign up. Please try again.')
            log_action(None, 'SIGNUP_FAILED', 'Failed signup attempt due to invalid form data.')
    else:
        form = SignUpForm()

    context = {'form': form}
    return render(request, 'Sign_up.html', context)

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
                log_action(user, 'LOGIN_SUCCESS', f"User logged in. Remember me: {remember_me}")

                if remember_me:
                    request.session.set_expiry(timedelta(days=7).total_seconds())
                else:
                    request.session.set_expiry(0)

                return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
                log_action(None, 'LOGIN_ATTEMPT', 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid form data. Please check your input.')
            log_action(None, 'LOGIN_ATTEMPT', 'Form validation failed.')

    else:
        form = AuthenticationForm()

    context = {'form': form}
    return render(request, 'Sign_in.html', context)

@login_required
def logout_view(request):
    log_action(request.user, 'LOGOUT', 'User logged out.')
    logout(request)
    return redirect('home')

@login_required
def chat_view(request):
    if request.method == "POST":
        user_query = request.POST.get("message", "")
        bot_reply = "Sorry, I'm having trouble connecting right now."

        try:
            response = requests.post(
                "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {HUGGING_FACE_API_KEY}"
                },
                json={"inputs": user_query},
            )
            response.raise_for_status()

            if isinstance(response.json(), list):
                bot_reply = response.json()[0].get("generated_text", "Sorry, I didn't understand that.")
            else:
                bot_reply = "Sorry, I didn't understand that."

        except requests.exceptions.RequestException as e:
            print(f"Error with chatbot API: {e}")

        ChatHistory.objects.create(
            user=request.user,
            query=user_query,
            response=bot_reply
        )
        log_action(request.user, 'CHAT_QUERY', f"Query: {user_query}, Response: {bot_reply}")

        return JsonResponse({"query": user_query, "response": bot_reply})

    return render(request, "home.html")

@login_required
def QueryHistory(request):
    user_history = ChatHistory.objects.filter(user=request.user).order_by('-timestamp')
    log_action(request.user, 'QUERY_HISTORY_VIEW', 'User viewed query history.')
    return render(request, 'query_history.html', {'history': user_history})

def FAQ(request):
    log_action(None, 'FAQ_VIEW', 'FAQ page viewed.')
    faq_data = [
        {
            'question': "What is land ownership in Uganda?",
            'answer': "Land ownership in Uganda is governed by the Land Act, which recognizes both customary and freehold land tenure systems. Individuals can own land either through a leasehold or freehold title, or under customary rights."
        },
        {
            'question': "How can I transfer land ownership?",
            'answer': "To transfer land ownership in Uganda, the current owner must have a registered title. The transfer involves signing a sale agreement, obtaining consent from the land office, and registering the transaction with the land registry."
        },
        {
            'question': "What is a land title deed?",
            'answer': "A land title deed is an official document issued by the Land Registry that confirms a person’s legal ownership of a piece of land. The title contains details such as the land's location, size, and ownership history."
        },
        {
            'question': "What is the difference between freehold and leasehold land?",
            'answer': "Freehold land is land owned outright and can be transferred, sold, or inherited. Leasehold land, on the other hand, is leased from the government or a private entity for a specific period, after which the lease can be renewed or reverted back."
        },
        {
            'question': "Can I use land without a title?",
            'answer': "Yes, land can be used without a title under customary land tenure systems, but the use is often less secure compared to titled land. It is advisable to register land to ensure proper ownership rights."
        },
        {
            'question': "What are land taxes in Uganda?",
            'answer': "Land owners in Uganda are required to pay annual land rent and taxes, including property taxes. These taxes are calculated based on the value of the land and the type of land tenure system it falls under."
        },
    ]

    return render(request, 'faq.html', {'faq_data': faq_data})

@login_required
def ExportPDF(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="chat_history.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    y = 750

    chats = ChatHistory.objects.filter(user=request.user).order_by('timestamp')
    p.drawString(100, 800, f"Chat History for {request.user.username}")

    for chat in chats:
        p.drawString(100, y, f"Date: {chat.timestamp}")
        y -= 20
        p.drawString(100, y, f"You: {chat.query}")
        y -= 20
        p.drawString(100, y, f"Bot: {chat.response}")
        y -= 40
        if y < 50:
            p.showPage()
            y = 750

    p.save()
    log_action(request.user, 'EXPORT_PDF', 'User exported chat history as PDF.')
    return response

@login_required()
def ExportCSV(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="chat_history.csv"'

    writer = csv.writer(response)
    writer.writerow(['User', 'Query', 'Response', 'Timestamp'])

    for chat in ChatHistory.objects.filter(user=request.user).order_by('timestamp'):
        writer.writerow([chat.user.username, chat.query, chat.response, chat.timestamp])

    log_action(request.user, 'EXPORT_CSV', 'User exported chat history as CSV.')

    return response

@login_required
def export_pdf_logs(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{request.user.username}_logs_history.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    y_position = 750

    logs = ActionLog.objects.filter(user=request.user).order_by('-timestamp')

    p.drawString(100, y_position, f"Logs History for {request.user.username}")
    y_position -= 40

    for log in logs:
        p.drawString(100, y_position, f"Timestamp: {log.timestamp}")
        y_position -= 20
        p.drawString(100, y_position, f"Action: {log.action_type}")
        y_position -= 20
        p.drawString(100, y_position, f"Details: {log.details}")
        y_position -= 30

        if y_position < 50:
            p.showPage()
            y_position = 750

    p.save()
    log_action(request.user, 'EXPORT_PDF', 'User exported logs history as PDF.')

    return response

import os

@login_required
def export_csv_logs(request):
    logs = ActionLog.objects.filter(user=request.user).order_by('-timestamp')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{request.user.username}_logs_history.csv"'

    writer = csv.writer(response)
    writer.writerow(['Timestamp', 'Action', 'Details'])

    for log in logs:
        writer.writerow([log.timestamp, log.action_type, log.details])

    log_action(request.user, 'EXPORT_CSV', 'User exported logs history as CSV.')

    return response


from django.shortcuts import render
import io
import unittest

def run_tests():
    stream = io.StringIO()
    test_suite = unittest.defaultTestLoader.loadTestsFromName('myapp.tests')
    test_result = unittest.TextTestRunner(stream=stream).run(test_suite)
    return test_result, stream.getvalue()

from django.http import JsonResponse
from django.shortcuts import render
import io
import unittest

def test_results(request):
    """
    Handles the test results page.
    - On GET: Renders the test results page with a loader.
    - On AJAX GET: Executes tests and returns results as JSON.
    """
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Handle the AJAX request to fetch test results
        test_result, test_output = run_tests()

        # Format the test results into JSON-compatible data
        data = {
            'test_output': test_output,  # Full console output of the tests
            'failures': [{'test': failure[0], 'details': failure[1]} for failure in test_result.failures],
            'errors': [{'test': error[0], 'details': error[1]} for error in test_result.errors],
            'tests_run': test_result.testsRun,
            'was_successful': test_result.wasSuccessful(),
        }

        return JsonResponse(data)

    # For regular GET, render the test results page with a loader
    return render(request, 'test_results.html')








