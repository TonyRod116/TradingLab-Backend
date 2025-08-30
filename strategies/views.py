from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Strategy
from .serializers import StrategySerializer
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticatedOrReadOnly

# Create your views here.
# Patch: /countries/
class StrategyView(APIView):
    
    permission_classes = [IsAuthenticatedOrReadOnly]

    # Index route
    # Method: GET
    def get(self, request):
        Strategys = Strategy.objects.all()
        serialized_Strategys = StrategySerializer(Strategys, many=True)
        return Response(serialized_Strategys.data)
    
    # Create route
    # Method: POST
    def post(self, request):
        serialized_Strategys = StrategySerializer(data=request.data)

        # is_valid does the following: 
        # 1. takes the request.data and tries to vlaidate it based on the model
        # 2. if it fails it returns false, also adds an error key onto the serialized_Strategys object
        # 3. if it succeeds it returns true, also adds the data key onto the serialized_Strategys object
        # 4. if we set the raise_exception to true, it will raise Rest Framework's own ValidationError exception
        # ? Remember, all Rest Framework exceptions are  automatically handled by APIView, sending the relevant response

        serialized_Strategys.is_valid(raise_exception=True)

        # if validations succeeds, we can save the data
        serialized_Strategys.save(owner=request.user)

        # if validations fails, we can access the errors
        # print(serialized_Strategys.errors)

        return Response(serialized_Strategys.data, status=201)




# Path: /countries/<int:pk>
class StrategyDetailView(APIView):

    permission_classes = [IsAuthenticatedOrReadOnly]

    #helper function that attempts to get the specified object, but sends a 404 if not found
    # 1. get_Strategy will take the PK from the URL params as an argument
    # 2. it will attempt to get the object from the database
    # 3. if it succeeds, it will return the object
    # 4. if it fails, it will raise a DoesNotExist exception then he will send a 404 by raising NotFound
    def get_Strategy(self,pk):
        try:
            return Strategy.objects.get(pk=pk)
        except Strategy.DoesNotExist as e:
            raise NotFound("Strategy does not exist")


    # Show route
    # Method: GET
    def get(self, request, pk):
        Strategy = Strategy.objects.get(pk=pk) # Country.findOne({ _id: req.params.countryId})
        serialized_Strategy = StrategySerializer(Strategy)
        return Response(serialized_Strategy.data)


    # Update route
    # Method: PUT
    def put(self, request, pk):
        Strategy = self.get_Strategy(pk)

        # after retrieving country from database, deny acces if the logged in user s not the owner
        if Strategy.owner != request.user:
            raise PermissionDenied("Unauthorized: You do not have permission to access this resource") #raising a PermissionDenied exception will automatically send a 403 Forbidden response

        # if the user is the owner, continue
        serialized_Strategy = StrategySerializer(Strategy, data=request.data)
        serialized_Strategy.is_valid(raise_exception=True)
        serialized_Strategy.save(owner=request.user)
        return Response(serialized_Strategy.data)  



    # Delete route
    # Method: DELETE
    def delete(self, request, pk):
        Strategy = self.get_Strategy(pk)
        
        if Strategy.owner != request.user:
            raise PermissionDenied("Unauthorized: You do not have permission to access this resource")

        Strategy.delete()
        return Response(status=204)
# Create your views here.

