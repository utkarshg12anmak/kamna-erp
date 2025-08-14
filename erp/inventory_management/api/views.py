from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from decimal import Decimal

from ..models import STN, STNDetail, STNStatus, STNStatusHistory
from ..utils import get_available_physical_qty
from .serializers import STNSerializer, STNDetailSerializer, STNStatusHistorySerializer
from .errors import INVALID_STATE_CHANGE, SOFT_DELETE_NOT_ALLOWED, CONFIRM_FAILED


class STNViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = STN.objects.select_related('source_warehouse', 'destination_warehouse').prefetch_related('lines', 'status_history')
    serializer_class = STNSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'status': ['exact'],
        'source_warehouse': ['exact'],
        'destination_warehouse': ['exact'],
        'created_at': ['date__gte', 'date__lte']
    }
    search_fields = ['stn_code', 'lines__sku__sku', 'lines__sku__name']
    ordering_fields = ['updated_at', 'created_at', 'stn_code']
    ordering = ['-updated_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        stn = self.get_object()
        if stn.status != STNStatus.DRAFT:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'code': INVALID_STATE_CHANGE,
                'detail': 'Only DRAFT STNs can be edited'
            })
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        stn = self.get_object()
        if stn.status != STNStatus.DRAFT:
            return Response({
                'code': INVALID_STATE_CHANGE,
                'detail': 'Only DRAFT STNs can be confirmed'
            }, status=400)

        # Re-check all lines against live availability
        shortages = []
        for line in stn.lines.select_related('sku'):
            available = get_available_physical_qty(line.sku_id, stn.source_warehouse_id)
            if line.created_qty > available:            shortages.append({
                'sku_id': line.sku_id,
                'sku': getattr(line.sku, 'sku', ''),
                'need': float(line.created_qty),
                'have': float(available),
                'short_by': float(line.created_qty - available)
            })

        if shortages:
            return Response({
                'code': CONFIRM_FAILED,
                'detail': 'Availability changed',
                'shortages': shortages
            }, status=400)

        # Update status and create history
        stn.status = STNStatus.CREATED
        stn.updated_by = request.user
        stn.save(update_fields=['status', 'updated_by', 'updated_at'])
        
        STNStatusHistory.objects.create(
            stn=stn,
            from_status=STNStatus.DRAFT,
            to_status=STNStatus.CREATED,
            changed_by=request.user
        )

        return Response(STNSerializer(stn).data)

    @action(detail=True, methods=['post'])
    def soft_delete(self, request, pk=None):
        stn = self.get_object()
        if stn.status != STNStatus.CREATED:
            return Response({
                'code': SOFT_DELETE_NOT_ALLOWED,
                'detail': 'Only CREATED STNs can be soft-deleted'
            }, status=400)

        if stn.sum_dispatched_qty and float(stn.sum_dispatched_qty) > 0:
            return Response({
                'code': SOFT_DELETE_NOT_ALLOWED,
                'detail': 'Cannot delete once any dispatch has occurred'
            }, status=400)

        # Update status and create history
        stn.status = STNStatus.DELETED
        stn.updated_by = request.user
        stn.save(update_fields=['status', 'updated_by', 'updated_at'])
        
        STNStatusHistory.objects.create(
            stn=stn,
            from_status=STNStatus.CREATED,
            to_status=STNStatus.DELETED,
            changed_by=request.user
        )

        return Response(STNSerializer(stn).data)


class STNDetailViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = STNDetailSerializer
    queryset = STNDetail.objects.select_related('stn', 'sku')
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {'stn': ['exact']}

    def get_serializer_context(self):
        context = super().get_serializer_context()
        stn_id = self.request.data.get('stn') or self.request.query_params.get('stn')
        if self.action == 'create' and stn_id:
            try:
                context['stn'] = STN.objects.get(id=stn_id)
            except STN.DoesNotExist:
                pass
        return context

    def perform_create(self, serializer):
        stn_id = self.request.data.get('stn')
        if stn_id:
            try:
                stn = STN.objects.get(id=stn_id)
                serializer.save(stn=stn)
            except STN.DoesNotExist:
                serializer.save()
        else:
            serializer.save()
