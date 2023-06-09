from core.models import Note,Client
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.serializers import NoteSerializer
from rest_framework.request import Request
from core.user_agent import parse,version_to_number
from core.consumers import note_updated
from datetime import datetime

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
        note_updated(request.uid,note.updated_at.strftime ("%Y-%m-%dT%H:%M:%S.%fZ"))
        return Response(NoteSerializer(note).data)
    
    def delete(self,request,pk):
        Note.objects.filter(id=pk).delete()
        now = datetime.now()
        note_updated(request.uid,now.strftime ("%Y-%m-%dT%H:%M:%S.%fZ"))
        return Response(status=status.HTTP_200_OK)

class ClientView(APIView):
    
    def put(self,request:Request,pk,format=None):
        client_type,client_version,os = parse(request.headers['user-agent'])
        client_version_num = version_to_number(client_version)
        
        Client.objects.get_or_create(
            defaults={
                "uid":request.uid,
                "client_type":client_type,
                "client_version":client_version_num,
                "os":os
            },
            client_id=pk,
            )
        client_count = Client.objects.filter(uid=request.uid).count()
        return Response({'client_count':client_count})