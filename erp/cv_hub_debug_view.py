from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

@login_required
def cv_hub_debug(request):
    """Debug view to check CV Hub access"""
    user = request.user
    groups = [g.name for g in user.groups.all()]
    
    context = {
        'user': user,
        'groups': groups,
        'has_cv_hub_group': 'Customer & Vendor Hub' in groups,
        'is_authenticated': user.is_authenticated,
        'is_superuser': user.is_superuser,
    }
    
    return render(request, 'cv_hub_debug.html', context)
