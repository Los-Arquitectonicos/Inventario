from django.utils import timezone
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse



# En views_.py
def healthCheck(request):
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0'
    })