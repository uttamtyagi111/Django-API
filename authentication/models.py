from django.utils.timezone import now
from django.db import models
from django.contrib.auth.models import User
import uuid


class PasswordResetToken(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return now() > self.expires_at

    def __str__(self):
        return f"Reset token for {self.user.username}"



class DeviceVerifyOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    device_id = models.IntegerField(null=True, blank=True)

    def is_expired(self):
        return now() > self.expires_at

    def __str__(self):
        return f"{self.user.email} - {self.otp} - {self.user.username}"
    

class LoginOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return now() > self.expires_at

    def __str__(self):
        return f"{self.user.email} - {self.otp}- {self.user.username}"
