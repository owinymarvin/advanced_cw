from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import ChatHistory, ActionLog


class AppTests(TestCase):

    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'password1': 'strongpassword123',
            'password2': 'strongpassword123'
        }
        self.user = User.objects.create_user(username='testuser', password='strongpassword123')

    def test_signup(self):
        response = self.client.post(reverse('signup'), data=self.user_data)
        self.assertEqual(response.status_code, 200)  # Should redirect after successful signup
        user = User.objects.get(username='testuser')
        self.assertIsNotNone(user)

    def test_signin(self):
        self.client.login(username='testuser', password='strongpassword123')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)  # Home page loads after login

    def test_logout(self):
        self.client.login(username='testuser', password='strongpassword123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)  # Should redirect after logout
    
    def test_chat(self):
        self.client.login(username='testuser', password='strongpassword123')
        response = self.client.post(reverse('home'), data={'message': 'Hello'})
        self.assertEqual(response.status_code, 200)  # Ensure the response status is OK
        self.assertTrue(response.content)  # Ensure that some content is returned


    def test_export_pdf(self):
        self.client.login(username='testuser', password='strongpassword123')
        response = self.client.get(reverse('export_pdf'))
        self.assertEqual(response.status_code, 200)  # PDF should be returned

    def test_export_csv(self):
        self.client.login(username='testuser', password='strongpassword123')
        response = self.client.get(reverse('export_csv'))
        self.assertEqual(response.status_code, 200)  # CSV should be returned

    def test_query_history(self):
        self.client.login(username='testuser', password='strongpassword123')
        response = self.client.get(reverse('query_history'))
        self.assertEqual(response.status_code, 200)  # Query history should be displayed

    def test_faq(self):
        response = self.client.get(reverse('FAQ'))
        self.assertEqual(response.status_code, 200)  # FAQ page should load

    def test_view_own_logs(self):
        self.client.login(username='testuser', password='strongpassword123')
        ActionLog.objects.create(user=self.user, action_type="LOGIN_SUCCESS", details="Logged in successfully")
        response = self.client.get(reverse('view_own_logs'))
        self.assertContains(response, 'LOGIN_SUCCESS')


    def test_export_pdf_logs(self):
        self.client.login(username='testuser', password='strongpassword123')
        ActionLog.objects.create(user=self.user, action_type="EXPORT_PDF", details="Exported logs")
        response = self.client.get(reverse('export_pdf_logs'))
        self.assertEqual(response.status_code, 200)  # PDF of logs should be generated

    def test_export_csv_logs(self):
        self.client.login(username='testuser', password='strongpassword123')
        ActionLog.objects.create(user=self.user, action_type="EXPORT_CSV", details="Exported logs to CSV")
        response = self.client.get(reverse('export_csv_logs'))
        self.assertEqual(response.status_code, 200)  # CSV of logs should be generated
