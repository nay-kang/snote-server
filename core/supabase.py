from supabase import create_client,Client
from django.conf import settings

client:Client = None
def get_client():
    global client
    if(client is None):
        client = create_client(settings.SUPABASE['url'],settings.SUPBASE['key'])
        
    return client