import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Team, Player

def index(request):
    max_slots = 12
    # Count teams with status 'Accepted' (1)
    approved_teams = Team.objects.filter(payment_status=1).count()
    available_slots = max_slots - approved_teams
    
    if available_slots < 0:
        available_slots = 0
    
    context = {
        'available_slots': available_slots
    }
    return render(request, 'tournament/index.html', context)

@ensure_csrf_cookie
def register(request):
    return render(request, 'tournament/register.html')

def api_register_team(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Extract data
            team_name = data.get('teamName')
            division = data.get('division')
            city = data.get('city')
            
            # Captain Info
            full_name = data.get('capName', '').strip()
            # Simple split for First/Last name
            name_parts = full_name.split(' ', 1)
            cap_first = name_parts[0]
            cap_last = name_parts[1] if len(name_parts) > 1 else ''
            
            phone = data.get('phone')
            email = data.get('email')
            roster_text = data.get('roster', '')

            # Basic Validation
            if Team.objects.filter(name=team_name).exists():
                return JsonResponse({'success': False, 'error': 'Team name already taken.'}, status=400)
            
            if Team.objects.filter(cap_email=email).exists():
                return JsonResponse({'success': False, 'error': 'This email is already registered.'}, status=400)

            # Create Team
            team = Team.objects.create(
                name=team_name,
                division=division,
                city=city,
                cap_name=cap_first,
                cap_surname=cap_last,
                cap_phone=phone,
                cap_email=email,
                payment_status=0 # Waiting
            )
            
            # Process Roster (Comma separated)
            # Format expected: "John Doe 10, Jane Smith 12"
            if roster_text:
                players = [p.strip() for p in roster_text.split(',') if p.strip()]
                for p_raw in players:
                    # Try to extract number if at the end
                    parts = p_raw.split()
                    number = None
                    last_name = ''
                    first_name = ''
                    
                    if parts:
                        # Check if last part is a number
                        if parts[-1].isdigit():
                            number = int(parts[-1])
                            name_parts = parts[:-1]
                        else:
                            name_parts = parts
                        
                        if name_parts:
                            first_name = name_parts[0]
                            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                            
                            Player.objects.create(
                                team=team,
                                first_name=first_name,
                                last_name=last_name,
                                jersey_number=number
                            )

            return JsonResponse({'success': True, 'team_id': team.id})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)
