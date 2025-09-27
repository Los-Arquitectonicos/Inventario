from django.shortcuts import render
from django.http import HttpResponse



def healthCheck(request):
    return HttpResponse('ok')