import csv
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth import (authenticate, login, logout, update_session_auth_hash)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.http import HttpResponse
from django.shortcuts import redirect, render
from .forms import SignUpForm
from django.core.files.storage import default_storage
from django.http import JsonResponse
from .models import ChatHistory
from django.contrib.auth.decorators import login_required
import requests

# Hardcoded Hugging Face API key
HUGGING_FACE_API_KEY = "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"

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
            messages.success(request, 'Your account has been created successfully!', extra_tags='success')
            return redirect('signin')
    else:
        form = SignUpForm()

    return render(request, 'Sign_up.html', {'form': form})

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
    return redirect('FAQ')

@login_required
def chat_view(request):
    if request.method == "POST":
        user_query = request.POST.get("message", "")
        
        # Default bot reply in case of error
        bot_reply = "Sorry, I'm having trouble connecting right now."

        try:
            # Call the chatbot API with the hardcoded API key
            response = requests.post(
                "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {HUGGING_FACE_API_KEY}"
                },
                json={"inputs": user_query},
            )
            response.raise_for_status()  # Raise an error for non-200 status codes
            
            # Debug: Print the response to check its structure
            print("API Response:", response.json())  # This will show the raw response

            # Adjusted to handle the response as a list
            if isinstance(response.json(), list):
                # If the response is a list, take the first item in the list
                bot_reply = response.json()[0].get("generated_text", "Sorry, I didn't understand that.")
            else:
                # In case the response is in a different format, default to the error message
                bot_reply = "Sorry, I didn't understand that."

        except requests.exceptions.RequestException as e:
            print(f"Error with chatbot API: {e}")
            # In case of error, we already have the default `bot_reply` message

        # Save the conversation in the database
        ChatHistory.objects.create(
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
    # Sample FAQ data
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

    # Render the FAQ template with the data
    return render(request, 'faq.html', {'faq_data': faq_data})


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

@login_required()
def ExportCSV(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="chat_history.csv"'

    writer = csv.writer(response)
    writer.writerow(['User', 'Query', 'Response', 'Timestamp'])

    for chat in ChatHistory.objects.filter(user=request.user).order_by('timestamp'):
        writer.writerow([chat.user.username, chat.query, chat.response, chat.timestamp])

    return response
