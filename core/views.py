from core.models import Note,Client
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.serializers import NoteSerializer
from rest_framework.request import Request
from core.user_agent import parse,version_to_number
from core.consumers import note_updated
from datetime import datetime
import re
from asgiref.sync import async_to_sync,sync_to_async

class NoteView(APIView):
    # permission_classes = []
    
    def get(self,request:Request,format=None):
        uid = request.uid
        filters = query_to_filter(request.query_params.dict()|request.data)
        filters['uid']=uid
        notes = Note.objects.filter(**filters).all()
        return Response(NoteSerializer(notes,many=True).data)
    
    @async_to_sync
    async def put(self,request,pk,format=None):
        '''
        I want return response first then send grpc
        but after tring async function I failed.
        '''
        data = request.data
        data['uid'] = request.uid
        data['status'] = Note.NoteStatus.NORMAL
        note,_ = await sync_to_async(Note.objects.update_or_create)(id=pk,defaults=data)
        await sync_to_async(note.save)()
        await note_updated(request.uid,note.updated_at.strftime ("%Y-%m-%dT%H:%M:%S.%fZ"))
        return await sync_to_async(Response)(NoteSerializer(note).data)
    
    def delete(self,request,pk):
        # direct update status will not trigger update_at
        # Note.objects.filter(id=pk).update(status=Note.NoteStatus.SOFT_DEL)
        now = datetime.now()
        note = Note.objects.get(id=pk)
        note.status=Note.NoteStatus.SOFT_DEL
        note.save()
        
        async_to_sync(note_updated)(request.uid,now.strftime ("%Y-%m-%dT%H:%M:%S.%fZ"))
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
    
    
def query_to_filter(querys:dict)->dict:
    '''
    https://gist.github.com/nay-kang/358e6e41858b5530a9cf
    '''
    filters = {}
    for k,v in querys.items():
        
        if m := re.match(r'^(\[|\()(.*):(.*)(\]|\))$',v):
            if m[2]:
                comp = 'gt' if m[1]=='(' else 'gte'
                filters[f'{k}__{comp}']=m[2]
            if m[3]:
                comp = 'lt' if m[4]=='(' else 'lte'
                filters[f'{k}__{comp}']=m[3]
        else:
            filters[k]=v
    return filters