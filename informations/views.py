from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import InformationAgricole
from .serializers import InformationAgricoleSerializer


class InformationAgricoleViewSet(viewsets.ModelViewSet):
    serializer_class = InformationAgricoleSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return InformationAgricole.objects.filter(
            actif=True
        ).order_by("-date_publication")

    def create(self, request, *args, **kwargs):
        url = request.data.get("url")

        # L'article existe déjà
        if url:
            information_existante = InformationAgricole.objects.filter(
                url=url
            ).first()

            if information_existante:
                serializer = self.get_serializer(information_existante)

                return Response(
                    serializer.data,
                    status=status.HTTP_200_OK
                )

        # Nouvel article
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )