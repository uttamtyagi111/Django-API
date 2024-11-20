from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class Plan(models.Model):
    name = models.CharField(max_length=100)
    email_limit = models.IntegerField(default=10)  # 10 emails for trial, unlimited for others
    device_limit = models.IntegerField(default=1)  # 1 device for basic, 3 for premium
    duration_days = models.IntegerField(default=30)  # 30 days expiration
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan_name = models.CharField(max_length=20, choices=[('Basic', 'Basic'), ('Premium', 'Premium')], null=True, blank=True)
    plan_status = models.CharField(max_length=20, default='inactive')
    emails_sent = models.IntegerField(default=0)
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True,unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True,unique=True)
    plan_expiration_date = models.DateTimeField(default=timezone.now() + timedelta(days=30))
    current_plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True)
    # refresh_token = models.TextField(null=True, blank=True)
    # system_info = models.JSONField(null=True, blank=True)
    
    DEFAULT_TRIAL_LIMIT = 10  

    def can_send_email(self):
        """Check if the user can send an email based on their plan and email limit."""

        # Trial users with no active plan
        if self.current_plan is None:
            if self.emails_sent > self.DEFAULT_TRIAL_LIMIT:
                self.plan_status = "expired"
                self.save()
                return False, "Trial limit exceeded. Please subscribe to a plan."
            return True, "You are on a trial; you can send more emails."

        if self.plan_expiration_date <= timezone.now():
            self.plan_status = "expired"
            self.save()
            return False, "Your subscription has expired. Please renew your plan."

        if self.current_plan.email_limit == 0:  # Check if the plan has unlimited email sending
            return True, "You have unlimited email sending capabilities."

        # Check if the emails sent are within the allowed limit
        if self.emails_sent < self.current_plan.email_limit:
            return True, "You can send emails."

        # Email limit exceeded
        self.plan_status = "expired"
        self.save()
        return False, "Plan expired . Please renew or upgrade your plan."


    def activate_plan(self, plan):
        """Activate a new plan for the user."""
        self.current_plan = plan  
        self.plan_name = plan.name  
        self.plan_status = 'active'  # Set the plan status to active
        self.plan_expiration_date = timezone.now() + timedelta(days=plan.duration_days)  # Set expiration date based on plan's duration
        self.emails_sent = 0  # Reset the emails sent counter
        self.save()  # Save the changes to the user profile

    def choose_plan_view(self, new_plan):
        """Subscribe the user to a selected plan."""
        self.activate_plan(new_plan) 
        self.save() 
        
    def increment_email_count(self):
        """Increment the number of emails sent by the user."""
        self.emails_sent += 1
        self.save()
        
    def check_plan_status(self):
        if self.plan_expiration_date < timezone.now():
            return 'Expired'        
        return 'Active'
    
class UserDevice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.TextField()
    device_name = models.CharField(max_length=100)  
    system_info = models.TextField()  
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.device_name} - {self.user.email}"




        
    
    
