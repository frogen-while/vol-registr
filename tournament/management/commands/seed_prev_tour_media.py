from django.core.management.base import BaseCommand
from tournament.models import GalleryPhoto, GalleryVideo
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Seeds media from assets/prev-tour into the database'

    def handle(self, *args, **options):
        prev_tour_dir = os.path.join(settings.BASE_DIR, 'static', 'assets', 'prev-tour')
        if not os.path.exists(prev_tour_dir):
            self.stdout.write(self.style.ERROR(f"Directory not found: {prev_tour_dir}"))
            return

        tag = 'prev-tour'
        files = os.listdir(prev_tour_dir)
        
        photos_created = 0
        videos_created = 0

        for filename in files:
            file_path = f"assets/prev-tour/{filename}"
            drive_url = f"/static/{file_path}"
            
            ext = os.path.splitext(filename)[1].lower()
            
            if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                obj, created = GalleryPhoto.objects.update_or_create(
                    drive_file_id=f"local_prev_{filename}",
                    defaults={
                        'title': f"Previous Tournament - {filename}",
                        'drive_url': drive_url,
                        'thumbnail_url': drive_url,
                        'tournament_tag': tag,
                        'media_state': 'featured'
                    }
                )
                if created: photos_created += 1
            
            elif ext in ['.mov', '.mp4', '.m4v']:
                obj, created = GalleryVideo.objects.update_or_create(
                    drive_file_id=f"local_prev_{filename}",
                    defaults={
                        'title': f"Previous Tournament Video - {filename}",
                        'drive_url': drive_url,
                        'thumbnail_url': '', # Could use a placeholder if we had one
                        'tournament_tag': tag,
                        'media_state': 'featured'
                    }
                )
                if created: videos_created += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {photos_created} photos and {videos_created} videos with tag '{tag}'"))
