# apps/auth_app/validators.py
"""
Validador de contraseña segura — SGEP V3.1
Aplica SOLO en: crear usuario, cambiar contraseña, restablecer contraseña.
NO afecta usuarios existentes. NO se invoca durante el login.
"""

import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class ContrasenaSeguraValidator:
    """
    Valida que la contraseña cumpla la política de seguridad del SGEP:
      - Mínimo 12 caracteres
      - Al menos una letra mayúscula (A-Z)
      - Al menos una letra minúscula (a-z)
      - Al menos un dígito (0-9)
      - Al menos un carácter especial (!@#$%^&*()_+-=[]{}|;:,.<>?)
    """

    MIN_LENGTH = 12
    ESPECIALES = r'[!@#$%^&*()\-_=+\[\]{}|;:,.<>?]'

    def validate(self, password, user=None):
        errores = []

        if len(password) < self.MIN_LENGTH:
            errores.append(_(f'La contraseña debe tener al menos {self.MIN_LENGTH} caracteres.'))

        if not any(c.isupper() for c in password):
            errores.append(_('La contraseña debe contener al menos una letra mayúscula.'))

        if not any(c.islower() for c in password):
            errores.append(_('La contraseña debe contener al menos una letra minúscula.'))

        if not any(c.isdigit() for c in password):
            errores.append(_('La contraseña debe contener al menos un número.'))

        if not re.search(self.ESPECIALES, password):
            errores.append(_('La contraseña debe contener al menos un carácter especial (!@#$%^&*...).'))

        if errores:
            raise ValidationError(errores)

    def get_help_text(self):
        return _(
            f'Su contraseña debe tener mínimo {self.MIN_LENGTH} caracteres, '
            'incluir mayúsculas, minúsculas, números y caracteres especiales.'
        )
