'''
the scene is A client generate for digit code, client B type this code and send to A over websocket by server
the ideal solution is using wamp to route the RPC call `verifyCode` from B to A, and A can immediately return code match or not.
but if using wamp to do this I had to introduce another component called `router`, 
and the rpc name is ugly due I had to made the client ID as part of rpc name, it can't using client ID as param
so I using django channels as a loose couple, message calls like `fire and forget`,
I need a timer to make sure the client not hanged by not getting the verify result.
'''
import functools
from channels_jsonrpc import JsonRpcWebsocketConsumer
from asgiref.sync import async_to_sync
from core.auth_middleware import verify_token
from inspect import getfullargspec
from django_redis import get_redis_connection
import time
from channels.layers import get_channel_layer

redis_db = get_redis_connection('redis_db')
channel_layer = get_channel_layer()

class ExchangeConsumer(JsonRpcWebsocketConsumer):
    
    def connect(self):
        self.accept()
    
    def disconnect(self, code):
        redis_db.hdel(f"user:${self.scope['uid']}",self.channel_name)
        async_to_sync(channel_layer.group_discard)(self.scope['uid'],self.channel_name)
        return super().disconnect(code)
    
    def aeskey_code_generate_notify(self,event):
        self.notify_channel('aeskeyCodeGenerate',{})
        
    def aeskey_code_verify(self,event):
        self.notify_channel('aeskeyCodeVerify',{
            "from":event['from'],
            'code':event['code']
        })
        
    def send_to_client(self,event):
        self.notify_channel('messageFromClient',{
            'from':event['from'],
            'message':event['message']
        })
        
    def note_updated(self,event):
        self.notify_channel('noteUpdated',{
            "eventAt":event['event_at']
        })
    
    @classmethod
    def check_auth(cls):
        
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args,**kwargs):
                consumer = kwargs['consumer']
                if not consumer.scope.get('uid'):
                    raise Exception('unauthorized')
                redis_db.hset(f"user:${consumer.scope['uid']}",consumer.channel_name,time.time())
                func_args = getattr(getfullargspec(func), 'varkw')
                if func_args and "kwargs" in func_args:
                    result = func(*args,**kwargs)
                else:
                    result = func(*args)
                
                return result

            return wrapper
        return decorator

@ExchangeConsumer.rpc_method()
@ExchangeConsumer.check_auth()
def ping():
    return 'Pong'

@ExchangeConsumer.rpc_method()
def auth(token,**kwargs):
    uid = verify_token(token)
    consumer = kwargs['consumer']
    consumer.scope['uid'] = uid
    redis_db.hset(f"user:${consumer.scope['uid']}",consumer.channel_name,time.time())
    async_to_sync(channel_layer.group_add)(uid,consumer.channel_name)
    print("group_add",uid,consumer.channel_name)
    return True

@ExchangeConsumer.rpc_method(rpc_name='prepareKeyExchange')
@ExchangeConsumer.check_auth()
def prepare_key_exchange(**kwargs):
    consumer = kwargs['consumer']
    uid = consumer.scope['uid']
    self_channel_name = consumer.channel_name
    clients = redis_db.hgetall(f"user:${uid}")
    for channel_name in clients:
        channel_name = channel_name.decode()
        if channel_name==self_channel_name:
            continue
        async_to_sync(channel_layer.send)(channel_name,{
            "type":"aeskey.code.generate.notify",
            "text":""
        })
    return True

@ExchangeConsumer.rpc_method(rpc_name='verifyAesExchangeCode')
@ExchangeConsumer.check_auth()
def verify_aes_exchange_code(code,**kwargs):
    consumer = kwargs['consumer']
    uid = consumer.scope['uid']
    self_channel_name = consumer.channel_name
    clients = redis_db.hgetall(f"user:${uid}")
    for channel_name in clients:
        channel_name = channel_name.decode()
        if channel_name==self_channel_name:
            continue
        async_to_sync(channel_layer.send)(channel_name,{
            "type":"aeskey.code.verify",
            "from":self_channel_name,
            "code":code,
        })
    return True

@ExchangeConsumer.rpc_method(rpc_name='sendToClient')
@ExchangeConsumer.check_auth()
def send_to_client(to,message,**kwargs):
    consumer = kwargs['consumer']
    self_channel_name = consumer.channel_name
    async_to_sync(channel_layer.send)(to,{
        "type":"send.to.client",
        "from":self_channel_name,
        "message":message,
    })
    return True

# this method should called by server
async def note_updated(uid,event_at):
    # async_to_sync(channel_layer.group_send)(
    #     uid,{
    #         "type":"note.updated",
    #         "event_at":event_at
    #     }
    # )

    await channel_layer.group_send(uid,{
            "type":"note.updated",
            "event_at":event_at
        })