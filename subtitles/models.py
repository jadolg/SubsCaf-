from __future__ import unicode_literals

from django.db import models

# Create your models here.

class Subtitulo(models.Model):
    nombre = models.CharField(max_length=500)
    # ruta = models.CharField(max_length=5000)
    descargas = models.IntegerField(default=0)
    ahash = models.CharField(max_length=64, unique=True)
    timestamp = models.DateTimeField(auto_now_add=True)