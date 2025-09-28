from django.core.management.base import BaseCommand, CommandError
from core.models import Note,Client
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from django.db.models import Min


class Command(BaseCommand):
    help = "Change expired soft delete to hard delete and remove expired hard delete notes"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show which notes would be affected without making changes',
        )

    def handle(self, *args, **options):
        self.mark_hard_deletions(**options)
        self.wipe_clients(**options)
        self.wipe_hard_deletions(**options)
            
    def mark_hard_deletions(self,**options):
        expire_days = getattr(settings, "SOFT_DELETE_EXPIRY_DAYS")
        expiration_date = timezone.now() - timedelta(days=expire_days)
        
        notes_to_wipe = Note.objects.filter(
            status=Note.NoteStatus.SOFT_DEL, updated_at__lt=expiration_date
        )
        count = notes_to_wipe.count()
        for note in notes_to_wipe:
            self.stdout.write(
                self.color(f"- Note ID: {note.id}, Last updated: {note.updated_at} , content size: {len(note.content)}",options['dry_run'])
            )
        self.stdout.write(
               self.color(f"Successfully mark {count} expired soft-deleted notes.",options['dry_run'])
            )
        if not options['dry_run']:
            notes_to_wipe.update(
                status=Note.NoteStatus.HARD_DEL, updated_at=timezone.now()
            )
            
    def wipe_clients(self,**options):
        expire_hours = getattr(settings, "JWT_REFRESH_EXPIRATION_HOURS")
        expiration_date = timezone.now() - timedelta(hours=expire_hours)
        
        clients_to_wipe = Client.objects.filter(
            updated_at__lt=expiration_date
        )
        count = clients_to_wipe.count()

        for client in clients_to_wipe:
            self.stdout.write(
                self.color(f"- Client ID: {client.client_id}, Last updated: {client.updated_at} , Info : {client.os}-{client.client_type}",options['dry_run'])
            )
        self.stdout.write(self.color(f"Successfully wiped {count} expired clients.",options['dry_run']))
        
        if not options['dry_run']:
            clients_to_wipe.delete()
            
    def wipe_hard_deletions(self,**options):
        oldest_clients = Client.objects.values("uid").annotate(oldest_update=Min("updated_at"))
        
        for client in oldest_clients:
            notes_to_wipe = Note.objects.filter(
                updated_at__lt=client['oldest_update'],
                uid=client['uid'],
                status=Note.NoteStatus.HARD_DEL
            )
            count = notes_to_wipe.count()
            if count == 0:
                continue
            self.stdout.write(self.color(f"Successfully purge hard delete note: uid {client['uid']} — removed {count} note(s).",options['dry_run']))
            if not options['dry_run']:
                notes_to_wipe.delete()
                
    def color(self,message,dry_run):
        if dry_run:
            return self.style.NOTICE(f"DRY RUN: {message}")
        return self.style.SUCCESS(message)