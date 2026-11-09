from datetime import timedelta
from django import forms
from django.utils import timezone
from .models import Player, PlaySession, BehaviorEvent


class AnalysisFilter(forms.Form):
    player_id = forms.ModelChoiceField(label='플레이어 선택', queryset=Player.objects.order_by('display_name', 'external_id'), required=False, empty_label='플레이어를 선택하세요')
    start = forms.DateField(label='시작일', widget=forms.DateInput(attrs={'type': 'date'}))
    end = forms.DateField(label='종료일', widget=forms.DateInput(attrs={'type': 'date'}))
    source = forms.ChoiceField(label='데이터', choices=[('all', '전체 (실제+데모)'), ('live', '실제 데이터'), ('demo', '데모 데이터')])
    topic = forms.ChoiceField(label='자료구조', required=False, choices=[('', '전체 자료구조')] + PlaySession.TOPICS)
    q = forms.CharField(label='플레이어 검색', required=False, max_length=150,
                        widget=forms.TextInput(attrs={'placeholder': '표시 이름 / 외부 ID'}))
    task_id = forms.CharField(label='문제 ID', required=False, max_length=80)
    content_version = forms.CharField(label='콘텐츠 버전', required=False, max_length=30)
    event_type = forms.ChoiceField(label='행동', required=False, choices=[('', '전체 행동')] + BehaviorEvent.TYPES)

    def __init__(self, data=None, *args, **kwargs):
        today = timezone.localdate()
        defaults = {'start': (today - timedelta(days=27)).isoformat(), 'end': today.isoformat(), 'source': 'all'}
        if data:
            defaults.update(data.dict() if hasattr(data, 'dict') else data)
        super().__init__(defaults, *args, **kwargs)
        self.fields['player_id'].label_from_instance = lambda p: f'{p.display_name} · {p.external_id} ({p.get_source_display()})'

    def clean(self):
        data = super().clean()
        if data.get('start') and data.get('end') and data['start'] > data['end']:
            raise forms.ValidationError('종료일은 시작일 이후여야 합니다.')
        if data.get('end') and data['end'] > timezone.localdate():
            self.add_error('end', '종료일은 오늘 이후일 수 없습니다.')
        return data
