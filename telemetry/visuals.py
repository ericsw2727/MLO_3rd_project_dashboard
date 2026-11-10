"""Chart-ready, filter-scoped observations. No simulated AI or inferred mastery."""
from collections import Counter, defaultdict
from datetime import timedelta
from math import ceil
from django.utils import timezone
from .learning import selected_runs
from .models import PlaySession
from .catalog import AREAS, area_for


def visual_report(form, players, events):
    if not form.is_valid():
        return {'empty': True, 'runs': 0, 'trend': [], 'outcomes': [], 'topics': [], 'versions': [],
                'histogram': [], 'attempts': [], 'failures': [], 'heatmap': [], 'scatter': [], 'hints': [], 'insights': []}
    runs=list(selected_runs(form,players).select_related('task','session__player').prefetch_related('attempts','events').order_by('started_at','id'))
    start,end=form.cleaned_data['start'],form.cleaned_data['end']
    days=(end-start).days+1;stride=max(1,ceil(days/45))
    daily=defaultdict(lambda:Counter());outcomes=Counter();topic=defaultdict(Counter);versions=defaultdict(Counter)
    histogram=Counter();attempt_bins=Counter();failures=Counter();scatter=[];hint_results=Counter();time_values=[]
    for run in runs:
        delta=(timezone.localdate(run.started_at)-start).days
        bucket=start+timedelta(days=(delta//stride)*stride)
        daily[bucket]['started']+=1;daily[bucket][run.status]+=1;outcomes[run.status]+=1
        area = area_for(run.task.task_id)
        topic[area]['n']+=1;topic[area]['solved']+=int(run.status=='completed')
        key=(run.task.task_id,run.task.content_version)
        versions[key]['n']+=1;versions[key]['solved']+=int(run.status=='completed')
        attempts=sorted(run.attempts.all(),key=lambda a:(a.started_at,a.number));attempt_bins[min(len(attempts),4)]+=1
        if run.status=='completed' and run.active_ms is not None:
            sec=run.active_ms/1000;time_values.append(sec)
            histogram[0 if sec<30 else 1 if sec<60 else 2 if sec<120 else 3 if sec<240 else 4]+=1
        run_events=list(run.events.all())
        for event in run_events:
            if event.event_type=='operation_failed':failures[(event.operation,event.failure_reason)]+=1
        hints=sorted([e for e in run_events if e.event_type=='hint'],key=lambda e:(e.occurred_at,e.sequence))
        if hints:
            after=next((a for a in attempts if a.started_at>hints[0].occurred_at),None)
            hint_results['success' if after and after.outcome=='success' else 'failure' if after and after.outcome=='failure' else 'unknown']+=1
        if run.active_ms is not None:
            scatter.append({'x':round(run.active_ms/1000,1),'y':len(attempts),'status':run.status,
                            'label':run.session.player.display_name,'task':run.task.task_id,'version':run.task.content_version})
    heat=Counter()
    for stamp in events.values_list('occurred_at',flat=True).iterator():
        stamp=timezone.localtime(stamp);heat[(stamp.weekday(),stamp.hour)]+=1
    topic_rows=[{'label':label,'n':topic[key]['n'],'rate':round(100*topic[key]['solved']/topic[key]['n'],1) if topic[key]['n'] else None} for key,label in AREAS + [('unmapped', '미분류')]]
    version_rows=[{'task':k[0],'version':k[1],'n':v['n'],'rate':round(100*v['solved']/v['n'],1)} for k,v in sorted(versions.items())]
    failure_rows=[{'label':f'{op} · {reason}','value':n} for (op,reason),n in failures.most_common(7)]
    insights=[]
    eligible=[v for v in version_rows if v['n']>=5]
    if eligible:
        worst=min(eligible,key=lambda r:r['rate'])
        insights.append({'title':'우선 관찰할 문제','value':f"{worst['task']} · v{worst['version']}", 'detail':f"해결률 {worst['rate']}% / 실행 {worst['n']}건. 난이도·표본 차이를 함께 확인하세요."})
    if failure_rows:
        insights.append({'title':'가장 많이 기록된 실패','value':failure_rows[0]['label'],'detail':f"{failure_rows[0]['value']}건. 개념 오류와 조작 오류의 원인 확인이 필요합니다."})
    n_hint=hint_results['success']+hint_results['failure']
    insights.append({'title':'힌트 다음 시도','value':f"{hint_results['success']} / {n_hint} 성공",'detail':f"평가 불가 {hint_results['unknown']}건은 분모에서 제외합니다. 힌트의 인과 효과는 아닙니다."})
    total_events=events.count();structured=events.filter(run__isnull=False).count()
    return {'empty':not runs,'runs':len(runs),'stride':stride,'trend':[{'label':(start+timedelta(days=i)).strftime('%m.%d'),
             'started':daily[start+timedelta(days=i)]['started'],'completed':daily[start+timedelta(days=i)]['completed'],
             'abandoned':daily[start+timedelta(days=i)]['abandoned']} for i in range(0,days,stride)],
            'outcomes':[{'label':label,'value':outcomes[k]} for k,label in [('completed','해결'),('abandoned','포기'),('in_progress','진행 중')]],
            'topics':topic_rows,'versions':version_rows,'histogram':[{'label':label,'value':histogram[i]} for i,label in enumerate(['30초 미만','30~60초','1~2분','2~4분','4분 이상'])],
            'attempts':[{'label':str(n) if n<4 else '4회 이상','value':attempt_bins[n]} for n in range(0,5)],
            'failures':failure_rows,'heatmap':[{'day':day,'hour':hour,'value':heat[(day,hour)]} for day in range(7) for hour in range(24)],
            'scatter':scatter[::max(1,ceil(len(scatter)/200))],'scatter_total':len(scatter),
            'hints':[{'label':label,'value':hint_results[k]} for k,label in [('success','다음 시도 성공'),('failure','다음 시도 실패'),('unknown','평가 불가')]],
            'quality':{'events':total_events,'structured':structured,'legacy':total_events-structured},'insights':insights}
