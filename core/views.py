from core.models import Note,Client
from rest_framework.views import APIView
from rest_framework.response import Response
from core.serializers import NoteSerializer
from rest_framework.request import Request

class NoteView(APIView):
    # permission_classes = []
    
    def get(self,request,format=None):
        uid = request.uid
        notes = Note.objects.filter(uid=uid).all()
        return Response(NoteSerializer(notes,many=True).data)
    
    def put(self,request,pk,format=None):
        data = request.data
        data['uid'] = request.uid
        note,_ = Note.objects.update_or_create(id=pk,defaults=data)
        note.save()
        return Response(NoteSerializer(note).data)

class ClientView(APIView):
    
    def put(self,request:Request,pk,format=None):
        Client.objects.get_or_create(client_id=pk,uid=request.uid)
        client_count = Client.objects.filter(uid=request.uid).count()
        return Response({'client_count':client_count})