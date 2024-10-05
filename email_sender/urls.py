from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import  SendEmailsView,UploadedFileList,UpdateUploadedFile
from . import views
from .views import UploadHTMLToS3

router = DefaultRouter()


urlpatterns = [
    path('', include(router.urls)),
    path('send-emails/', SendEmailsView.as_view(), name='send-emails'),
    path('smtp-servers/', views.smtp_servers_list, name='smtp-servers-list'),
    path('smtp-servers/<int:pk>/', views.smtp_server_detail, name='smtp-server-detail'),
    path('smtp-server/create/', views.smtp_server_create, name='smtp-server-create'),
    path('smtp-servers/edit/<int:pk>/', views.smtp_server_edit, name='smtp-server-edit'),
    path('smtp-servers/delete/<int:pk>/', views.smtp_server_delete, name='smtp-server-delete'),
    path('upload-html/', UploadHTMLToS3.as_view(), name='upload-html'),
    path('uploaded-files/', UploadedFileList.as_view(), name='uploaded-file-list'),
    path('uploaded-files/update/<int:file_id>/', UpdateUploadedFile.as_view(), name='update-uploaded-file'),
 ]
