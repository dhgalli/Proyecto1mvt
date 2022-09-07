from django.http import HttpResponse
from django.shortcuts import render
from .models import Curso

# Create your views here.
def curso(request):

    curso=Curso(nombre='Clase de matematica', comision=1)
    curso.save()
    texto=f'Clase creada: nombre: {curso.nombre} comision= {curso.comision}'
    return HttpResponse(texto)