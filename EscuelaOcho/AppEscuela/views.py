from django.http import HttpResponse
from django.shortcuts import render
from .models import Curso

# Create your views here.
def curso(request):

    curso=Curso(nombre='Clase de matematica', comision=1)
    curso.save()
    texto=f'Clase creada: nombre: {curso.nombre} comision= {curso.comision}'
    return HttpResponse(texto)

def inicio(request):
    return render (request, "AppEscuela/inicio.html")

def cursos(request):
    return render(request, "AppEscuela/cursos.html")

def profesores(request):
    return render(request, "AppEscuela/profesores.html")

def estudiantes(request):
    return render(request, "AppEscuela/estudiantes.html")

def entregables(request):
    return render(request, "AppEscuela/entregables.html")
