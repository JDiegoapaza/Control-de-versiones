# apps/auth_app/forms.py
"""
Formularios de gestión de usuarios — SGEP V3.1
Integrados en auth_app. Reutilizan modelos Usuario y Rol existentes.
Aplican ContrasenaSeguraValidator en creación y restablecimiento.
"""

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Usuario, Rol


class UsuarioCrearForm(forms.ModelForm):
    """
    Formulario para crear un nuevo usuario del sistema.
    Aplica validación de contraseña fuerte.
    Solo accesible para superusuarios.
    """
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mínimo 12 caracteres',
            'autocomplete': 'new-password',
        }),
        help_text='Mínimo 12 caracteres, mayúscula, minúscula, número y carácter especial.',
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repita la contraseña',
            'autocomplete': 'new-password',
        }),
    )

    class Meta:
        model = Usuario
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'cedula', 'rol', 'telefono', 'especialidad',
            'centro_penitenciario', 'activo',
        ]
        widgets = {
            'username':             forms.TextInput(attrs={'class': 'form-control'}),
            'first_name':           forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':            forms.TextInput(attrs={'class': 'form-control'}),
            'email':                forms.EmailInput(attrs={'class': 'form-control'}),
            'cedula':               forms.TextInput(attrs={'class': 'form-control'}),
            'rol':                  forms.Select(attrs={'class': 'form-select'}),
            'telefono':             forms.TextInput(attrs={'class': 'form-control'}),
            'especialidad':         forms.TextInput(attrs={'class': 'form-control'}),
            'centro_penitenciario': forms.TextInput(attrs={'class': 'form-control'}),
            'activo':               forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if password:
            # Dispara AUTH_PASSWORD_VALIDATORS de settings (incluye ContrasenaSeguraValidator)
            validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise ValidationError({'password2': 'Las contraseñas no coinciden.'})
        return cleaned_data

    def save(self, commit=True, creado_por='sistema'):
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data['password1'])
        usuario.creado_por = creado_por
        if commit:
            usuario.save()
        return usuario


class UsuarioEditarForm(forms.ModelForm):
    """
    Formulario para editar datos de un usuario existente.
    NO cambia la contraseña (campo separado para eso).
    """
    class Meta:
        model = Usuario
        fields = [
            'first_name', 'last_name', 'email',
            'cedula', 'rol', 'telefono', 'especialidad',
            'centro_penitenciario', 'activo',
        ]
        widgets = {
            'first_name':           forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':            forms.TextInput(attrs={'class': 'form-control'}),
            'email':                forms.EmailInput(attrs={'class': 'form-control'}),
            'cedula':               forms.TextInput(attrs={'class': 'form-control'}),
            'rol':                  forms.Select(attrs={'class': 'form-select'}),
            'telefono':             forms.TextInput(attrs={'class': 'form-control'}),
            'especialidad':         forms.TextInput(attrs={'class': 'form-control'}),
            'centro_penitenciario': forms.TextInput(attrs={'class': 'form-control'}),
            'activo':               forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class UsuarioResetPasswordForm(forms.Form):
    """
    Formulario para que el superusuario restablezca la contraseña de otro usuario.
    Aplica validación de contraseña fuerte.
    """
    password1 = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mínimo 12 caracteres',
            'autocomplete': 'new-password',
        }),
    )
    password2 = forms.CharField(
        label='Confirmar nueva contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repita la contraseña',
            'autocomplete': 'new-password',
        }),
    )

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if password:
            validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise ValidationError({'password2': 'Las contraseñas no coinciden.'})
        return cleaned_data
