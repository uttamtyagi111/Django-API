import base64
import hashlib
import json
import requests
from django.http import JsonResponse, HttpResponseBadRequest
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .utils import send_email_with_pdf
from django.conf import settings
from datetime import timedelta
import razorpay
import logging
from .models import Plan, UserProfile
from razorpay.errors import BadRequestError, ServerError



logger = logging.getLogger(__name__)
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        plan_status = user_profile.check_plan_status()
        
        data = {
            'username': request.user.username,
            'email_count': user_profile.emails_sent,
            'plan_name': user_profile.plan_name,
            'plan_status': plan_status,
            'plan_start_date' : user_profile.plan_start_date,
            'plan_expiry_date': user_profile.plan_expiration_date
            
        }
        return Response(data, status=status.HTTP_200_OK)
    except UserProfile.DoesNotExist:
        return Response({'message': 'User profile not found.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def get_available_plans(request):
    plans = Plan.objects.all()
    data = [{'id': plan.id, 'name': plan.name, 'email_limit': plan.email_limit, 'duration_days': plan.duration_days} for plan in plans]
    return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def choose_plan_view(request):
    """
    Allows authenticated users to choose a plan.
    """
    plan_name = request.data.get('plan_name')
    
    if plan_name not in ['Basic','Standard', 'Premium','Elite']:
        return Response({'message': 'Invalid plan selected. Choose either "Basic" or "Standard"or "Premium"or "Elite".'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:

        user_profile = UserProfile.objects.get(user=request.user)
        plan = Plan.objects.get(name__iexact=plan_name)
        
        user_profile.plan_name = plan.name
        user_profile.current_plan = plan
        user_profile.plan_status = "active"
        user_profile.emails_sent = 0
        user_profile.plan_start_date = timezone.now()  
        user_profile.plan_expiration_date = timezone.now() + timedelta(days=plan.duration_days)
        user_profile.save()

        return Response({'message': f'Plan successfully updated to {plan_name}.'}, status=status.HTTP_200_OK)
    except UserProfile.DoesNotExist:
        return Response({'message': 'User profile not found.'}, status=status.HTTP_404_NOT_FOUND)
    except Plan.DoesNotExist:
        return Response({'message': 'Selected plan not found.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def upgrade_plan(request):
    """
    Allows authenticated users to upgrade to a new plan.
    """
    plan_name = request.data.get('plan_name')

    # List of available plans with an order to ensure upgrades are happening correctly
    available_plans = ['Basic', 'Standard', 'Premium', 'Elite']

    if plan_name not in available_plans:
        return Response({'message': 'Invalid plan selected. Choose from "Basic", "Standard", "Premium", or "Elite".'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user_profile = UserProfile.objects.get(user=request.user)
        new_plan = Plan.objects.get(name__iexact=plan_name)

        # Check if the new plan is actually an upgrade
        current_plan_index = available_plans.index(user_profile.plan_name)
        new_plan_index = available_plans.index(new_plan.name)

        if new_plan_index <= current_plan_index:
            return Response({'message': 'You can only upgrade to a higher plan.'}, status=status.HTTP_400_BAD_REQUEST)

        # Carry forward remaining email count from the previous plan
        # remaining_emails = user_profile.email_limit - user_profile.emails_sent
        current_expiration_date = user_profile.plan_expiration_date
        # Update the user profile with the new plan
        user_profile.plan_name = new_plan.name
        user_profile.current_plan = new_plan
        user_profile.plan_status = "initiated"
        # user_profile.emails_sent = 0  # Reset email count
        user_profile.email_limit += new_plan.email_limit  # New email limit (old emails + new plan's limit)
        user_profile.plan_start_date = timezone.now()
        user_profile.plan_expiration_date = current_expiration_date 
        user_profile.save()

        # # Optional: Send an email notification to the user
        # send_email_with_pdf(
        #     transaction_id=f'upgrade_{timezone.now().strftime("%Y%m%d%H%M%S")}',
        #     plan_name=new_plan.name,
        #     price=new_plan.price,
        #     expiry_date=user_profile.plan_expiration_date,
        #     user_email=user_profile.user.email
        # )

        return Response({'message': f'Plan successfully upgraded to {plan_name}.'}, status=status.HTTP_200_OK)

    except UserProfile.DoesNotExist:
        return Response({'message': 'User profile not found.'}, status=status.HTTP_404_NOT_FOUND)
    except Plan.DoesNotExist:
        return Response({'message': 'Selected plan not found.'}, status=status.HTTP_404_NOT_FOUND)
          



# Logger instance
logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    """
    Creates a Razorpay order for the selected plan and updates the user profile with billing details.
    """
    try:
        # Get data from request
        data = request.data
        plan_name = data.get('plan_name')

        # Billing Address Fields
        address_line1 = data.get("address_line1")
        address_line2 = data.get("address_line2", "")  # Optional field
        city = data.get("city")
        state = data.get("state")
        zip_code = data.get("zip_code")
        country = data.get("country")

        # Validate plan selection
        valid_plans = ['Basic', 'Standard', 'Premium', 'Elite']
        if plan_name not in valid_plans:
            return Response(
                {'message': f'Invalid plan selected. Choose from {valid_plans}.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate billing address fields
        if not all([address_line1, city, state, zip_code, country]):
            return Response({'message': 'All billing address fields except address_line2 are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the selected plan
        try:
            plan = Plan.objects.get(name__iexact=plan_name)
        except Plan.DoesNotExist:
            return Response({'message': 'Selected plan not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Create Razorpay Order
        order_amount = int(plan.price * 100)  # Convert amount to paise
        order_currency = 'INR'
        order_receipt = f'order_rcptid_{request.user.id}'

        razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))
        razorpay_order = razorpay_client.order.create({
            'amount': order_amount,
            'currency': order_currency,
            'receipt': order_receipt,
            'payment_capture': '1'
        })

        # Save order & billing details in the user's profile
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            user_profile.current_plan = plan
            user_profile.razorpay_order_id = razorpay_order['id']
            user_profile.payment_status = "initiated"

            # Update billing address fields
            user_profile.address_line1 = address_line1
            user_profile.address_line2 = address_line2
            user_profile.city = city
            user_profile.state = state
            user_profile.zip_code = zip_code
            user_profile.country = country

            user_profile.save()
        except Exception as e:
            logger.error(f'Error updating user profile: {e}')
            return Response({'message': 'Error updating user profile.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Return order details for frontend processing
        return Response({
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'amount': order_amount,
            'currency': order_currency,
            'plan_name': plan.name,
            'billing_details': {
                'address_line1': address_line1,
                'address_line2': address_line2,
                'city': city,
                'state': state,
                'zip_code': zip_code,
                'country': country
            },
            'message': f'Order created successfully for the {plan_name} plan with billing details.'
        }, status=status.HTTP_200_OK)

    except BadRequestError as e:
        logger.error(f'Bad Request: {e}')
        return Response({'message': 'Error creating Razorpay order due to bad request.'}, status=status.HTTP_400_BAD_REQUEST)
    
    except ServerError as e:
        logger.error(f'Server Error: {e}')
        return Response({'message': 'Error creating Razorpay order due to a server issue.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        logger.error(f'Unexpected Error: {e}')
        return Response({'message': 'An unexpected error occurred while creating the order.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_payment_callback(request):
    payload = request.data
    razorpay_order_id = payload.get('razorpay_order_id')
    razorpay_payment_id = payload.get('razorpay_payment_id')
    razorpay_signature = payload.get('razorpay_signature')

    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))

    try:
        razorpay_client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        })
        try:
            user_profile = UserProfile.objects.get(razorpay_order_id=razorpay_order_id)
        except UserProfile.DoesNotExist:
            return Response({'message': 'Order not found for this user profile.'}, status=404)

        plan = user_profile.current_plan
        user_profile.plan_name = plan.name
        user_profile.plan_start_date = timezone.now()
        user_profile.plan_expiration_date = timezone.now() + timedelta(days=plan.duration_days)
        user_profile.plan_status = 'active'
        user_profile.payment_status = 'paid'
        user_profile.razorpay_payment_id = razorpay_payment_id
        user_profile.save()
        
        send_email_with_pdf(
            transaction_id=razorpay_payment_id,
            plan_name=plan.name,
            price=plan.price,
            expiry_date=user_profile.plan_expiration_date,
            user_email=user_profile.user.email
        )


        return Response({'message': 'Payment successful, plan activated!'}, status=200)

    except razorpay.errors.SignatureVerificationError:
        return Response({'message': 'Invalid payment signature.'}, status=400)

    except Exception as e:
        return Response({'message': 'An error occurred during payment processing.'}, status=500)



VERIFY_URL = settings.VERIFY_URL
MERCHANT_ID = settings.MERCHANT_ID
SALT_KEY = settings.SALT_KEY
PHONEPE_URL = settings.PHONEPE_URL


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_payment(request):
    try:
        # Extract form data safely
        data = request.data
        merchant_transaction_id = data.get("transactionId")
        name = data.get("name")
        amount = data.get("amount")
        mobile = data.get("mobile")
        plan_name = data.get("plan_name")

        # Billing Address Fields
        address_line1 = data.get("address_line1")
        address_line2 = data.get("address_line2", "") 
        city = data.get("city")
        state = data.get("state")
        zip_code = data.get("zip_code")
        country = data.get("country")

        # Validate required fields
        required_fields = {
            "transactionId": merchant_transaction_id, "name": name, "mobile": mobile,
            "plan_name": plan_name, "address_line1": address_line1, "city": city,
            "state": state, "zip_code": zip_code, "country": country
        }
        missing_fields = [field for field, value in required_fields.items() if not value]

        if missing_fields:
            return JsonResponse({"error": "Missing required fields", "missing_fields": missing_fields}, status=400)

        # Convert amount to paise
        try:
            amount = int(amount) * 100
        except ValueError:
            return JsonResponse({"error": "Invalid amount format"}, status=400)

        # Validate selected plan
        valid_plans = ['Basic', 'Standard', 'Premium', 'Elite']
        if plan_name not in valid_plans:
            return Response({'message': f'Invalid plan selected. Choose from {valid_plans}.'}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the selected plan
        try:
            plan = Plan.objects.get(name__iexact=plan_name)
        except Plan.DoesNotExist:
            return JsonResponse({"error": "Plan not found"}, status=404)

        # Ensure user has a profile
        user_profile = UserProfile.objects.get(user=request.user)
        # Check if the user already has the same plan
        if user_profile.current_plan and user_profile.current_plan.name == plan_name:
            return JsonResponse({"error": f"You have already purchased the {plan_name} plan."}, status=400)
        # Update billing address
        user_profile.address_line1 = address_line1
        user_profile.address_line2 = address_line2
        user_profile.city = city
        user_profile.state = state
        user_profile.zip_code = zip_code
        user_profile.country = country

        # Construct PhonePe payment payload
        payload = {
            "merchantId": MERCHANT_ID,
            "merchantTransactionId": merchant_transaction_id,
            "message": "Payment Initiated",
            "name": name,
            "amount": amount,
            "redirectUrl": f"http://localhost:8000/verify-payment/?id={merchant_transaction_id}",
            "redirectMode": "POST",
            "callbackUrl": f"http://localhost:8000/payment-success?id={merchant_transaction_id}",
            "mobileNumber": mobile,
            "paymentInstrument": {"type": "PAY_PAGE"},
        }

        # Encode payload and generate checksum
        payload_encoded = base64.b64encode(json.dumps(payload).encode()).decode()
        checksum_string = f"{payload_encoded}/pg/v1/pay{SALT_KEY}"
        checksum_hash = hashlib.sha256(checksum_string.encode()).hexdigest()
        checksum = f"{checksum_hash}###1"

        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "X-VERIFY": checksum,
        }
        api_payload = {"request": payload_encoded}

        # Call PhonePe API
        response = requests.post(PHONEPE_URL, headers=headers, json=api_payload)
        response_data = response.json()

        if response.status_code == 200 and response_data.get("success"):
            # Update user profile with transaction details
            user_profile.phonepe_transaction_id = merchant_transaction_id
            user_profile.current_plan = plan
            user_profile.plan_status = "inactive"  # Until payment is confirmed
            user_profile.payment_status = "initiated"
            user_profile.pending_plan_id = plan.id
            user_profile.save()

            redirect_url = response_data["data"]["instrumentResponse"]["redirectInfo"]["url"]
            return JsonResponse({"redirect_url": redirect_url}, status=200)
        else:
            return JsonResponse(response_data, status=response.status_code)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



import hashlib
import requests
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import redirect

from rest_framework.permissions import AllowAny

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_payment(request):
    try:
        merchant_transaction_id = request.GET.get("id")
        if not merchant_transaction_id:
            return JsonResponse({"error": "Transaction ID is required"}, status=400)

        # Generate checksum for verifying the payment
        checksum_string = f"/pg/v1/status/{MERCHANT_ID}/{merchant_transaction_id}{SALT_KEY}"
        checksum_hash = hashlib.sha256(checksum_string.encode()).hexdigest()
        checksum = f"{checksum_hash}###1"

        # Prepare headers for the API call
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "X-VERIFY": checksum,
            "X-MERCHANT-ID": MERCHANT_ID,
        }

        # Call PhonePe API to verify payment status
        response = requests.get(f"{VERIFY_URL}/{MERCHANT_ID}/{merchant_transaction_id}", headers=headers)
        response_data = response.json()

        if response_data.get("success"):
            # Extract payment status
            payment_status = response_data.get("data", {}).get("status", "").lower()

            # Find the user profile associated with the transaction
            user_profile = UserProfile.objects.get(phonepe_transaction_id=merchant_transaction_id)

            if payment_status == "":
                # Retrieve the plan details from the database
                plan = Plan.objects.get(id=user_profile.pending_plan_id)  # Assuming `pending_plan_id` was saved earlier

                user_profile.activate_plan(plan)
                
                send_email_with_pdf(
                transaction_id=merchant_transaction_id,
                plan_name=plan.name,
                price=plan.price,
                expiry_date=user_profile.plan_expiration_date,
                user_email=user_profile.user.email
                )


                # Redirect or respond with success
                return redirect("http://localhost:8000/payment-success")
            else:
                # Handle failed or pending payments
                user_profile.plan_status = "inactive"
                user_profile.payment_status = payment_status    
                user_profile.save()

                return redirect("http://localhost:8000/payment-failed")
        else:
            # API call failed, log the error and return failure
            return JsonResponse({"error": response_data.get("message", "Payment verification failed.")}, status=400)

    except Plan.DoesNotExist:
        return JsonResponse({"error": "Selected plan does not exist."}, status=404)
    except UserProfile.DoesNotExist:
        return JsonResponse({"error": "Transaction ID not associated with any user profile."}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


from django.shortcuts import render

def payment_success(request):
    """Handle successful payments."""
    return render(request, 'subscriptions/success.html')

def payment_failed(request):
    """Handle failed payments."""
    return render(request, 'subscriptions/failed.html')

