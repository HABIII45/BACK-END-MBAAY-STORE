from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .serializers import AdminLoginSerializer


class AdminLoginView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = AdminLoginSerializer(
            data=request.data
        )

        if serializer.is_valid():

            user = serializer.validated_data["user"]

            return Response(
                {
                    "message": "Connexion administrateur réussie.",
                    "access": str(
                        serializer.validated_data["access"]
                    ),
                    "refresh": str(
                        serializer.validated_data["refresh"]
                    ),
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "nom": user.nom,
                        "prenom": user.prenom,
                        "role": user.role,
                        "is_staff": user.is_staff,
                        "is_superuser": user.is_superuser,
                    }
                },
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )