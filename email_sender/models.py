from django.db import models
from django.conf import settings




from django.db import models
from django.contrib.auth.models import User

class UploadedFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to the user who uploaded the file
    name = models.CharField(max_length=255)  # Store the file name
    file_url = models.URLField(max_length=1024)  # Store the file URL (S3 URL)
    uploaded_at = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return self.name




class Sender(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()

    def __str__(self):
        return self.name

class SMTPServer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    host = models.CharField(max_length=255)
    port = models.PositiveIntegerField()
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    use_tls = models.BooleanField(default=True)
    # use_ssl = models.BooleanField(default=False)

    def __str__(self):
        return self.name
