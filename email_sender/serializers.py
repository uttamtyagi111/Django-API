from rest_framework import serializers
from .models import  SMTPServer,UploadedFile,EmailStatusLog,ContactFile,Campaign
        
class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ['id', 'user_id', 'name','key', 'file_url']  


class EmailStatusLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailStatusLog
        fields = ['id','user', 'email', 'status', 'timestamp', 'from_email', 'smtp_server']



class SMTPServerSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMTPServer
        fields = ['id', 'name', 'host', 'port', 'username', 'password', 'use_tls']


        

from rest_framework import serializers
from .models import Campaign, ContactFile, SMTPServer


# class ContactFileSerializer(serializers.ModelSerializer):
#     """Serializer to represent contact file details."""
#     class Meta:
#         model = ContactFile
#         fields = ['id', 'name']  # Include any fields you want to expose


from rest_framework import serializers

class CampaignSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255) 
    smtp_server_ids = serializers.ListField(
        child=serializers.IntegerField(),  
        write_only=True
    )
    display_name = serializers.CharField()  
    subject = serializers.CharField(max_length=255) 
    delay_seconds = serializers.IntegerField(required=False, default=0) 
    uploaded_file_key = serializers.CharField() 
    contact_list = serializers.PrimaryKeyRelatedField(queryset=ContactFile.objects.all()) 
    
    def validate_contact_list(self, value):
        if not ContactFile.objects.filter(id=value).exists():
            raise serializers.ValidationError("The provided contact file ID does not exist.")
        return value

    def validate_smtp_server_ids(self, value):
        if not value:
            raise serializers.ValidationError("At least one SMTP server ID must be provided.")
        invalid_ids = [id for id in value if not SMTPServer.objects.filter(id=id).exists()]
        if invalid_ids:
            raise serializers.ValidationError(f"Invalid SMTP server IDs: {invalid_ids}")
        return value

    def create(self, validated_data):
        smtp_server_ids = validated_data.pop('smtp_server_ids', [])
        campaign = Campaign.objects.create(**validated_data)
        campaign.smtp_servers.set(SMTPServer.objects.filter(id__in=smtp_server_ids))
        return campaign

    def update(self, instance, validated_data):
        smtp_server_ids = validated_data.pop('smtp_server_ids', [])
        
        for attr, value in validated_data.items():
            if attr != "smtp_servers":
                setattr(instance, attr, value)

        if smtp_server_ids:
            instance.smtp_servers.set(SMTPServer.objects.filter(id__in=smtp_server_ids))

        instance.save()
        return instance

    def validate(self, data):
        if not data.get('smtp_server_ids'):
            raise serializers.ValidationError("At least one SMTP server ID is required.")
        
        if data.get('delay_seconds', 0) < 0:
            raise serializers.ValidationError("Delay seconds cannot be negative.")
        
        return data

    def validate_campaign_name(self, value):
        """Ensure the campaign name is unique for the user."""
        request = self.context.get('request')
        if request and hasattr(request, "user"):
            if Campaign.objects.filter(name=value, user=request.user).exists():
                raise serializers.ValidationError("A campaign with this name already exists for the user.")
        return value

    
from rest_framework import serializers
from .models import Contact

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'contact_file', 'data']
