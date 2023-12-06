from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api import views

app_name = 'api'

router = DefaultRouter()
router.register('accounts', views.AccountViewSet)
router.register('loan', views.LoanViewSet)

# router.register('transaction', views.TrasactionViewSet)

# api = views.AccountViewSet.as_view({
#     'get': 'list',
#     'post': 'create'
# })


urlpatterns = [
    path('', include(router.urls)),
]
