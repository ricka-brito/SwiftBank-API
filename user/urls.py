from django.urls import path
from user import views

app_name = 'user'

urlpatterns = [
    path('create/', views.CreateUserView.as_view(), name='create-user'),
    path('me/', views.ManagerUserAPiView.as_view(), name='me'),
    # path('me/upload-image/', views.ManagerUserAPiView.as_view(), name='upload-image'),  # Manually define the URL for the action
]
