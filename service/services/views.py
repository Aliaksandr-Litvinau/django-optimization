from django.db.models import Prefetch, F, Sum
from rest_framework.viewsets import ReadOnlyModelViewSet

from clients.models import Client
from services.models import Subscription
from services.serializers import SubscriptionSerializer


class SubscriptionView(ReadOnlyModelViewSet):
    queryset = (
        Subscription.objects.all()
        .prefetch_related(
            "plan",
            # "service",
            Prefetch(
                "client",
                queryset=Client.objects.all()
                .select_related("user")
                .only("company_name", "user__email"),
            )
        )
        .annotate(
            price=F("service__full_price")  # the price value is calculated at the database level in the queryset
            - F("service__full_price") * F("plan__discount_percent") / 100
        )
    )

    serializer_class = SubscriptionSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        response = super().list(request, *args, **kwargs)
        response_data = {"result": response.data}
        response_data["total_amount"] = queryset.aggregate(total=Sum("price")).get("total")  # at the database level
        response.data = response_data
        return response
