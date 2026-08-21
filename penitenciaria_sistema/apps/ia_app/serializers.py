# apps/ia_app/serializers.py
from rest_framework import serializers
from .models import PrediccionRiesgo


class PrediccionRiesgoSerializer(serializers.ModelSerializer):
    nivel_riesgo_display = serializers.CharField(source='get_nivel_riesgo_display', read_only=True)

    class Meta:
        model = PrediccionRiesgo
        fields = '__all__'
        read_only_fields = ['id', 'fecha_prediccion']
