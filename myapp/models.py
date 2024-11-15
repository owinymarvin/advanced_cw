from django.contrib.auth.models import User
from django.db import models

class ChatHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Deletes history if user is removed
    query = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.timestamp}"

class ActionLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # Retain logs as anonymous
    action_type = models.CharField(max_length=20)  # Now accepts action type up to 20 characters
    details = models.TextField(blank=True, null=True)  # Additional details (optional)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        user_display = self.user.username if self.user else "Anonymous"
        return f"{user_display} - {self.action_type} - {self.timestamp}"
