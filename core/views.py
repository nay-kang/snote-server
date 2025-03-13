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
import gzip
from rest_framework.parsers import JSONParser
import secrets
from .serializers import EmailOTPSerializer
from django.core.mail import send_mail
from django.core.cache import cache
import time
from .auth_backend import otp_cache_key
from rest_framework.permissions import IsAuthenticated
import logging

def generate_verification_code():
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])

class GZipParser(JSONParser):
    media_type = '*/*'

    def parse(self, stream, media_type=None, parser_context=None):
        request:Request = parser_context['request']
        if request.headers.get('Content-Encoding')=='gzip':
            gzip_file = gzip.GzipFile(fileobj=stream)
            stream = gzip_file
        try:
            return super().parse(stream,media_type,parser_context)
        except Exception as err:
            logging.error(err)
        

class NoteView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [GZipParser]
    
    
    def get(self,request:Request,format=None):
        uid = request.user.id
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
        data['uid'] = request.user.id
        data['status'] = Note.NoteStatus.NORMAL
        note,_ = await sync_to_async(Note.objects.update_or_create)(id=pk,defaults=data)
        await sync_to_async(note.save)()
        await note_updated(request.user.id,note.updated_at.strftime ("%Y-%m-%dT%H:%M:%S.%fZ"))
        return await sync_to_async(Response)(NoteSerializer(note).data)
    
    def delete(self,request,pk):
        # direct update status will not trigger update_at
        # Note.objects.filter(id=pk).update(status=Note.NoteStatus.SOFT_DEL)
        now = datetime.now()
        note = Note.objects.get(id=pk)
        note.status=Note.NoteStatus.SOFT_DEL
        note.save()
        
        async_to_sync(note_updated)(request.user.id,now.strftime ("%Y-%m-%dT%H:%M:%S.%fZ"))
        return Response(status=status.HTTP_200_OK)

class ClientView(APIView):
    permission_classes = [IsAuthenticated]
    
    def put(self,request:Request,pk,format=None):
        client_type,client_version,os = parse(request.headers['user-agent'])
        client_version_num = version_to_number(client_version)
        
        Client.objects.get_or_create(
            defaults={
                "uid":request.user.id,
                "client_type":client_type,
                "client_version":client_version_num,
                "os":os
            },
            client_id=pk,
            )
        client_count = Client.objects.filter(uid=request.user.id).count()
        return Response({'client_count':client_count})
    
class EmailOTPView(APIView):
    permission_classes = []
    
    def post(self,request):
        serializer = EmailOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        code = generate_verification_code()
        cache_key = otp_cache_key(email)
        cached_code = cache.get(cache_key)
        #do not allow user resend code in 60 seconds
        if cached_code and time.time()-cached_code['ts']<60:
            return Response({"code":"prevent_resend_code_intime"},status=status.HTTP_403_FORBIDDEN)
        send_mail('SNote login code',f'Your code is {code}','notify@codeedu.net',[email],fail_silently=False)
        cache.set(cache_key,{"code":code,"ts":time.time()},60*5)
        return Response(status=status.HTTP_200_OK)


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