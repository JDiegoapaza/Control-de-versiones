# apps/internos_app/serializers.py
from rest_framework import serializers
from .models import Interno


class InternoSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Interno
        fields = '__all__'
        read_only_fields = ['id', 'creado_en', 'actualizado_en', 'fecha_registro']

    def get_nombre_completo(self, obj) -> str:
        return obj.nombre_completo()
