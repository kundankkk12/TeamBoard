from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q, Count
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Company, KBEntry, QueryLog
from .permissions import IsAdminUser


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def register_company(request):
    """Register a new company and return initial credentials + JWT."""
    username = request.data.get('username')
    password = request.data.get('password')
    company_name = request.data.get('company_name')
    email = request.data.get('email')

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

    # 1. Create User (Signal auto-creates Company and api_key)
    user = User.objects.create_user(username=username, password=password, email=email)
    
    # 2. Update company details (role defaults to CLIENT per the model)
    company = user.company
    company.company_name = company_name
    company.save()

    # 3. Generate JWT Access Token
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    return Response({
        "username": user.username,
        "company_name": company.company_name,
        "api_key": company.api_key,
        "access": access_token
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def login_company(request):
    """Authenticate via username/password and return a fresh JWT."""
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)
    
    if user is None:
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        
    company = user.company
    refresh = RefreshToken.for_user(user)
    
    return Response({
        "access": str(refresh.access_token),
        "company_name": company.company_name,
        "api_key": company.api_key
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def query_kb(request):
    """Search the Knowledge Base and log the query atomically."""
    search_term = request.data.get('search', '').strip()
    
    if not search_term:
        return Response({"error": "Search term is missing or blank"}, status=status.HTTP_400_BAD_REQUEST)

    company = request.user.company

    # Keep search, count, and logging in one transaction for consistency.
    with transaction.atomic():
        entries = KBEntry.objects.filter(
            Q(question__icontains=search_term) | Q(answer__icontains=search_term)
        )
        results = [
            {
                "id": str(entry.id),
                "question": entry.question,
                "answer": entry.answer,
                "category": entry.category
            }
            for entry in entries
        ]
        count = len(results)
        
        # Always log the query, even if count is 0
        QueryLog.objects.create(
            company=company,
            search_term=search_term,
            results_count=count
        )

    return Response({
        "search": search_term,
        "count": count,
        "results": results
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def usage_summary(request):
    """Platform-wide usage statistics (Admin Only)."""
    
    total_queries = QueryLog.objects.aggregate(total=Count('id'))['total'] or 0
    active_companies = QueryLog.objects.values('company').distinct().count()
    
    # Group by search_term, count occurrences, and take top 5
    top_search_terms = list(
        QueryLog.objects.values('search_term')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )

    return Response({
        "total_queries": total_queries,
        "active_companies": active_companies,
        "top_search_terms": top_search_terms
    }, status=status.HTTP_200_OK)