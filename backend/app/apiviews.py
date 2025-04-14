from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import FormSerializer
from .scraper import ResultScraperService

class ScraperAPIView(APIView):
    def post(self, request, *args, **kwargs):
        formserializer = FormSerializer(data=request.data)
        if formserializer.is_valid():
            prefix_usn = formserializer.validated_data["usn"].upper()
            usn_range = formserializer.validated_data["range"]
            url = formserializer.validated_data["url"]
            is_reval = "RV" in url
            scraper_service = ResultScraperService()
            
            try:
                df = scraper_service.execute_scraping(prefix_usn, usn_range, url, is_reval)
                
                if df is not None and not df.empty:
                    response = scraper_service.create_excel_response(df)
                    
                    response['X-Response-Type'] = 'file'
                    return response
                else:
                    return Response(
                        {"status": "error", "message": "No data was retrieved. Please check your inputs."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            except Exception as e:
                return Response(
                    {"status": "error", "message": f"Error during scraping: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            return Response(
                {"status": "error", "errors": formserializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )