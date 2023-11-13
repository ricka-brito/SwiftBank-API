"""
Serializer for the user API.
"""
from django.contrib.auth import get_user_model, authenticate
from core.models import Address

from rest_framework import serializers

from django.utils.translation import gettext as _ 


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['street', 'neighborhood', 'house_number', 'city', 'complement', 'cep', 'reference', 'uf']

class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user object"""
    addresses = AddressSerializer(many=True)
    class Meta:
        model = get_user_model()
        fields = ['email', 'password', 'first_name', 'last_name', 'cpf', 'created_at', 'url_imagem', 'phone_number', 'declared_salary', 'addresses']
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 6, 'max_length': 6},
            'is_active': {'read_only': True},
            'created_at': {'read_only': True},
            'addresses': {'write_only': True},
        }
    
    def create(self, validated_data):
        """Create and return a new user with the encrypted password."""
        address_data = validated_data.pop('addresses')
        user = get_user_model().objects.create_user(**validated_data)
        for i in address_data:
            address = Address.objects.create(**i)
            # Adiciona o endereço ao usuário criado
            user.addresses.add(address)

        return user
    
    def update(self, instance, validated_data):
        """Update and return a user."""
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        
        if password:
            user.set_password(password)
            user.save()
                    
        return user
    
    