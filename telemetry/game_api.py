"""Receive verified identities from a trusted game backend, never a Unity client."""
import json

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.utils.crypto import constant_time_compare
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from .models import Player
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_datetime
from .models import PlaySession, LearningTask, TaskRun, SolveAttempt, BehaviorEvent
from .recording import create_record, record_event, finalize_run, finish_record
from .mongo import get_record


@csrf_exempt
@never_cache
def player_login(request):
    if request.method != 'POST':
        response = JsonResponse({'error': 'method_not_allowed'}, status=405)
        response['Allow'] = 'POST'
        return response
    server_api_key = settings.GAME_SERVER_API_KEY
    if not server_api_key:
        return JsonResponse({'error': 'game_integration_disabled'}, status=503)
    if not constant_time_compare(request.headers.get('Authorization', ''), f'Bearer {server_api_key}'):
        return JsonResponse({'error': 'invalid_server_credentials'}, status=401)
    if request.content_type != 'application/json':
        return JsonResponse({'error': 'application_json_required'}, status=415)
    try:
        if int(request.META.get('CONTENT_LENGTH') or 0) > 4096 or len(request.body) > 4096:
            return JsonResponse({'error': 'payload_too_large'}, status=413)
        member_profile = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'error': 'invalid_json'}, status=400)
    if not isinstance(member_profile, dict) or set(member_profile) != {'member_id', 'display_name'}:
        return JsonResponse({'error': 'expected_member_id_and_display_name'}, status=400)
    member_id, display_name = member_profile['member_id'], member_profile['display_name']
    if (not isinstance(member_id, str) or not member_id or len(member_id) > 120
            or not member_id.isascii()
            or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.@' for c in member_id)):
        return JsonResponse({'error': 'invalid_member_id'}, status=400)
    if (not isinstance(display_name, str) or not display_name.strip()
            or len(display_name) > 80 or any(ord(c) < 32 for c in display_name)):
        return JsonResponse({'error': 'invalid_display_name'}, status=400)
    # Prefix prevents external identities from claiming existing demo/device records.
    with transaction.atomic():
        game_member, was_created = Player.objects.select_for_update().get_or_create(
            external_id=f'game:member:{member_id}',
            defaults={'display_name': display_name.strip(), 'source': 'live'},
        )
        if game_member.source != 'live':
            return JsonResponse({'error': 'player_source_conflict'}, status=409)
        if game_member.display_name != display_name.strip():
            game_member.display_name = display_name.strip()
            game_member.save(update_fields=['display_name'])
    return JsonResponse({'player': {
        'player_id': str(game_member.pk), 'member_id': member_id,
        'display_name': game_member.display_name, 'source': game_member.source,
    }, 'created': was_created}, status=201 if was_created else 200)


@csrf_exempt
@never_cache
def game_records(request):
    if request.method != 'POST':
        response = JsonResponse({'error': 'method_not_allowed'}, status=405)
        response['Allow'] = 'POST'
        return response
    server_api_key = settings.GAME_SERVER_API_KEY
    if not server_api_key:
        return JsonResponse({'error': 'game_integration_disabled'}, status=503)
    if not constant_time_compare(request.headers.get('Authorization', ''), f'Bearer {server_api_key}'):
        return JsonResponse({'error': 'invalid_server_credentials'}, status=401)
    if request.content_type != 'application/json':
        return JsonResponse({'error': 'application_json_required'}, status=415)
    if int(request.META.get('CONTENT_LENGTH') or 0) > 65536 or len(request.body) > 65536:
        return JsonResponse({'error': 'payload_too_large'}, status=413)
    try:
        envelope = json.loads(request.body)
        if not isinstance(envelope, dict) or set(envelope) != {'record_type', 'data'}:
            raise ValueError
        record_type, record_fields = envelope['record_type'], envelope['data']
        if not isinstance(record_type, str) or not isinstance(record_fields, dict):
            raise ValueError
        if record_type in ('end_run', 'end_attempt', 'end_session'):
            if set(record_fields) != {'id', 'status', 'ended_at'} or not isinstance(record_fields['ended_at'], str):
                raise ValueError
            from uuid import UUID
            record_id = UUID(record_fields['id'])
            ended_at = parse_datetime(record_fields['ended_at'])
            if ended_at is None:
                raise ValueError
            model = {'end_run': TaskRun, 'end_attempt': SolveAttempt, 'end_session': PlaySession}[record_type]
            if model is TaskRun:
                result = finalize_run(get_record(model, record_id), record_fields['status'], ended_at)
            else:
                result = finish_record(model, record_id, record_fields['status'], ended_at)
            return JsonResponse({'record_id': str(result.pk), 'status': 'finalized'})
        record_models = {'session': PlaySession, 'problem': LearningTask, 'run': TaskRun,
                  'attempt': SolveAttempt, 'event': BehaviorEvent}
        if record_type not in record_models:
            raise ValueError
        model = record_models[record_type]
        allowed = {field.attname: field for field in model._meta.concrete_fields if field.name != 'received_at'}
        if 'id' not in record_fields or set(record_fields) - set(allowed):
            raise ValueError
        validated_fields = {name: (allowed[name].target_field if allowed[name].is_relation else allowed[name]).to_python(value)
                   for name, value in record_fields.items()}
        if record_type in ('session', 'run') and validated_fields.get('status', 'in_progress') != 'in_progress':
            raise ValueError
        if record_type in ('session', 'run'):
            validated_fields['status'] = 'in_progress'
        if record_type == 'attempt':
            if validated_fields.get('outcome', 'in_progress') != 'in_progress':
                raise ValueError
            validated_fields['outcome'] = 'in_progress'
        if record_type in ('session', 'run', 'attempt') and validated_fields.get('ended_at') is not None:
            raise ValueError
        if record_type == 'event':
            result, was_created = record_event(**validated_fields)
        else:
            result, was_created = create_record(model(**validated_fields))
        return JsonResponse({'record_id': str(result.pk), 'created': was_created}, status=201 if was_created else 200)
    except (ValueError, TypeError, UnicodeDecodeError, ValidationError, Player.DoesNotExist):
        return JsonResponse({'error': 'invalid_or_conflicting_record'}, status=400)
