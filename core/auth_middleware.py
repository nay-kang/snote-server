from .firebase import auth as fire_auth
from core.models import Auth
from django.core.exceptions import ObjectDoesNotExist
from django.http.response import HttpResponse
import json
from channels.security.websocket import WebsocketDenier

# @database_sync_to_async
def verify_token(token):
    try:
        auth_record = Auth.objects.get(pk=token)
        return auth_record.uid
    except ObjectDoesNotExist:
        decoded_token = fire_auth.verify_id_token(token)
        uid = decoded_token['uid']
        auth_record = Auth(
            token=token,
            uid=uid,
            expired_at=decoded_token['exp']
        )
        auth_record.save()
        return uid
    
class AuthMiddleware:
    
    def __init__(self,get_response) -> None:
        self.get_response = get_response
        
    def __call__(self, request) -> any:
        if request.path=='/':
            return self.get_response(request)
        
        token:str = request.META['HTTP_AUTHORIZATION']
        token = token.replace('Bearer','').strip()
        uid = verify_token(token)
        if uid is None:
            return HttpResponse('',status=401)
        request.uid = uid
        response = self.get_response(request)
        return response
    
@DeprecationWarning    
class AuthMiddlewareWS:
    '''
    channels middleware only work when the first connect,it will not work by every receive
    '''
    def __init__(self,app) -> None:
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope.get('uid'):
            return await self.app(scope,receive,send)
        d = json.loads(receive)
        token = d['token']
        uid = verify_token(token)
        if uid is None:
            denier = WebsocketDenier()
            return await denier(scope, receive, send)
        #do nothing after validate user
        pass
        