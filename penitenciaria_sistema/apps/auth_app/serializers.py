# apps/auth_app/serializers.py
"""
Serializers de autenticación y usuarios.
"""

from rest_framework import serializers
from .models import Usuario, Rol, SesionUsuario


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = '__all__'


class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer completo del usuario (sin contraseña)."""
    rol_nombre = serializers.CharField(source='rol.nombre', read_only=True)
    nombre_completo = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'cedula', 'rol', 'rol_nombre', 'nombre_completo',
            'activo', 'bloqueado', 'telefono', 'especialidad',
            'centro_penitenciario', 'ultimo_login', 'creado_por',
        ]
        read_only_fields = ['id', 'ultimo_login', 'creado_por']


class LoginSerializer(serializers.Serializer):
    """Serializer para el login vía API."""
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, write_only=True)


class SesionUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = SesionUsuario
        fields = '__all__'
        read_only_fields = ['id', 'fecha_creacion']
