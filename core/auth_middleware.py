from .supabase import get_client as get_supa_client
from core.models import Auth
from django.http.response import HttpResponse
import json
from channels.security.websocket import WebsocketDenier
from datetime import datetime
from django_redis import get_redis_connection
from pottery import Redlock

# @database_sync_to_async
def verify_token(token):
    access_token = token[:-22]
    refresh_token = token[-22:]
    redis_client = get_redis_connection()
    lock = Redlock(key=token,masters={redis_client})
    with lock:
        try:
            auth_record = Auth.objects.filter(token=access_token).first()
            if not auth_record:
                client = get_supa_client()
                session = client.auth.set_session(access_token,'')
                auth_record = Auth(
                    token=token,
                    uid=session.user.id,
                    expired_at=datetime.fromtimestamp(session.session.expires_at)
                )
                auth_record.save()
                return session.user.id
        except Exception as err:
            print(err)
            return None
        return auth_record.uid
    
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
        