from rest_framework import serializers
from core import models
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model,authenticate

class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Note
        fields = ['id','uid','content','created_at','updated_at','status']
        
class EmailOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

class SnoteTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = get_user_model().USERNAME_FIELD

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].required = False
        self.fields['code'] = serializers.CharField(required=True)

    def validate(self, attrs):
        # Remove password from validation
        if 'password' in attrs:
            del attrs['password']

        email = attrs.get('email')
        code = attrs.get('code')

        if not email or not code:
            raise serializers.ValidationError('Email and code are required')

        # Use Django's authentication backend
        credentials = {
            'email': email,
            'code': code
        }
        try:
            credentials["request"] = self.context["request"]
        except KeyError:
            pass
        
        user = authenticate(**credentials)
        
        if user is None:
            raise serializers.ValidationError('Invalid email or code')

        refresh = self.get_token(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        return token

