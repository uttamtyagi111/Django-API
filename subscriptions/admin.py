from django.contrib import admin
from .models import Plan, UserProfile

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name','price','duration_days','email_limit','device_limit')
    search_fields = ('name','price')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan_name', 'plan_status', 'emails_sent', 'plan_expiration_date')
    search_fields = ('user__username', 'user__email')
    list_filter = ('plan_name', 'plan_status')
    readonly_fields = ('emails_sent', 'razorpay_order_id')
    
    def plan_name(self, obj):
        return obj.current_plan.name if obj.current_plan else 'No Plan Assigned'
    plan_name.short_description = 'Plan Name'

# from django.contrib import admin
# from .models import Order

# class OrderAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user', 'razorpay_order_id', 'razorpay_payment_id', 'payment_amount', 'payment_status', 'plan_name', 'payment_date')
#     search_fields = ('razorpay_order_id', 'razorpay_payment_id', 'user__username', 'plan_name')
#     list_filter = ('payment_status', 'plan_name', 'payment_date')
#     readonly_fields = ('user', 'razorpay_order_id', 'razorpay_payment_id', 'payment_amount',  'payment_status', 'plan_name', 'payment_date')

#     # Customize the detail view layout
#     fieldsets = (
#         (None, {
#             'fields': ('user', 'plan_name', 'razorpay_order_id', 'razorpay_payment_id')
#         }),
#         ('Payment Details', {
#             'fields': ('payment_amount',  'payment_status', 'payment_date')
#         }),
#     )

# admin.site.register(Order, OrderAdmin)