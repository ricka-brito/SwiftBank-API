"""
Serializer for the user API.
"""
import decimal
import random
from django.contrib.auth import get_user_model, authenticate
from core.models import Address, CreditCard

from rest_framework import serializers

from django.utils.translation import gettext as _ 

from core.models import LoginAttempt
from core.models import Account
from datetime import timedelta
from django.utils import timezone
from api.serializers import AccountDetailSerializer


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['street', 'neighborhood', 'house_number', 'city', 'complement', 'cep', 'reference', 'uf']

class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user object"""
    addresses = AddressSerializer(many=True)
    account = AccountDetailSerializer(read_only=True)
    class Meta:
        model = get_user_model()
        fields = ['id','email', 'password', 'first_name', 'cpf', 'created_at', 'url_imagem', 'phone_number', 'declared_salary', 'addresses', 'account']
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 6, 'max_length': 6},
            'is_active': {'read_only': True},
            'created_at': {'read_only': True},
            'addresses': {'write_only': True},
            'account': {'read_only': True},
            'id': {'read_only': True}
        }
    
    def create(self, validated_data):
        """Create and return a new user with the encrypted password."""
        address_data = validated_data.pop('addresses')

        user = get_user_model().objects.create_user(**validated_data)
        for i in address_data:
            address = Address.objects.create(**i)
            # Adiciona o endereço ao usuário criado
            user.addresses.add(address)
        agency = '0001'
        number = ''
        for n in range(8):
            number += str(random.randint(0, 9))
            
        account = Account(
            user=user,
            number=number,
            agency=agency,
            balance=decimal.Decimal(0)
        )
                
        account.save()
        
        card = CreditCard(
            account=account,
            limit=validated_data['declared_salary']*15
        )
        card.save()
        return user
    
    def update(self, instance, validated_data):
        """Update and return a user."""
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        
        if password:
            user.set_password(password)
            user.save()
                    
        return user
    
    # def validate(self, data):
    #     user = authenticate(
    #         username=data.get('cpf'),
    #         password=data.get('password')
    #     )

    #     if user is None:
    #         # ip_address = self.context['request'].META.get('REMOTE_ADDR')
    #         LoginAttempt.objects.create(
    #             username=data.get('cpf'),
    #             successful=False
    #         )

    #         recent_attempts = LoginAttempt.objects.filter(
    #             username=data.get('cpf'),
    #             successful=False,
    #             timestamp__gte=timezone.now() - timedelta(minutes=10)
    #         ).count()

    #         if recent_attempts >= 3:
    #             last_failed_attempt = LoginAttempt.objects.filter(
    #                 username=data.get('cpf'),
    #                 successful=False
    #             ).latest('timestamp')

    #             time_elapsed = timezone.now() - last_failed_attempt.timestamp
    #             if time_elapsed < timedelta(minutes=5):
    #                 raise serializers.ValidationError(
    #                     _("Too many login attempts. Try again later.")
    #                 )

    #     return data
    
class CpfVerifierSerializer(serializers.Serializer):
    cpf = serializers.CharField()

    class Meta:
        fields = ['cpf']
        
class ImageUpdateSerializer(serializers.Serializer):
    img = serializers.ImageField()
    
    class Meta:
        fields = ['img']