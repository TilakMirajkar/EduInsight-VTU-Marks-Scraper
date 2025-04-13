from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import FormSerializer
from .scraper import ResultScraperService


class ScraperAPIView(APIView):
    def post(self, request, *args, **kwargs):
        """Handle POST request to scrape VTU results."""
        serializer = FormSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"status": "error", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        prefix_usn = serializer.validated_data["usn"].upper()
        usn_range = serializer.validated_data["range"]
        url = serializer.validated_data["url"]
        is_reval = "RV" in url.upper()
        print(f"Starting scrape for USN {prefix_usn}, range {usn_range}")

        scraper_service = ResultScraperService()
        try:
            df = scraper_service.execute_scraping(prefix_usn, usn_range, url, is_reval)
            if df is not None and not df.empty:
                print("Scraping successful, generating Excel.")
                return scraper_service.create_excel_response(df)
            return Response(
                {
                    "status": "error",
                    "message": "No data retrieved. Check USN, range, or URL.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            print(f"Scraping error: {str(e)}")
            return Response(
                {"status": "error", "message": f"Scraping failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )