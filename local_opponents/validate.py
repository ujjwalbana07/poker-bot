import subprocess,os,time,urllib.request,json,pathlib,argparse
parser=argparse.ArgumentParser()
parser.add_argument('--phase',choices=['before','after','baselines'],required=True)
parser.add_argument('--deals',type=int,default=1000)
options=parser.parse_args()
root=str(pathlib.Path(__file__).resolve().parent.parent); os.chdir(root); py=root+'/venv/bin/python'; env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=root); out=pathlib.Path('/tmp/poker-v2-'+options.phase); out.mkdir(exist_ok=True)
def start(path,port,label):
 log=open(out/(label+'.server.log'),'w'); started=time.perf_counter()
 p=subprocess.Popen([py,path],env=dict(env,PORT=str(port)),stdout=log,stderr=subprocess.STDOUT)
 try:
  while time.perf_counter()-started<15:
   if p.poll() is not None: raise RuntimeError('server exited: '+label)
   try:
    urllib.request.urlopen('http://127.0.0.1:'+str(port),timeout=.2).close(); return p,time.perf_counter()-started
   except Exception: time.sleep(.05)
  raise RuntimeError('startup timeout: '+label)
 except BaseException:
  p.terminate(); p.wait(); raise
 finally: log.close()
rows=[]
opponents = ({name: 'baseline-bots/baseline_'+name+'.py' for name in ['random','always_half','always_pot','calling_station']} if options.phase=='baselines' else {name: 'local_opponents/'+name+'.py' for name in ['tight_passive','loose_aggressive','pot_raiser_folder','benchmark']})
for bot, opponent_path in opponents.items():
 for seed in [1,7,21,99]:
  label=f'{bot}-{seed}'; a=b=None
  try:
   a,astart=start('local_opponents/benchmark.py' if options.phase=='before' else 'agent.py',5008,label+'-agent')
   b,bstart=start(opponent_path,5009,label+'-baseline')
   args=[py,'judge_engine.py','--deals',str(options.deals),'--seed',str(seed),'--json',str(out/(label+'.json')),'--logs']
   r=subprocess.run(args,env=env,capture_output=True,text=True)
   (out/(label+'.report.txt')).write_text(r.stdout+r.stderr)
   if r.returncode: raise RuntimeError('judge failed '+label+' '+r.stdout+r.stderr)
   d=json.loads((out/(label+'.json')).read_text()); stats=d['agent_stats']['agent1']; allstats=[s for ss in d['agent_stats'].values() for s in ss]
   row=dict(bot=bot,seed=seed,result=d['verdict'],bb=d['mean_bb_per_deal'],ci=d['ci'],errors=[s['errors'] for s in stats],thinking=[s['time_seconds'] for s in stats],forfeited=any(s['forfeited'] for s in allstats),empty=any(s['timed_out'] for s in allstats),startup=astart,avg_ms=1000*sum(s['wall_seconds'] for s in stats)/sum(s['calls'] for s in stats))
   row['passed']=row['result']=='AGENT1_WIN' and not any(s['errors'] for s in allstats) and not row['forfeited'] and not row['empty'] and max(row['thinking'])<4 and row['avg_ms']<2
   rows.append(row); (out/'summary.json').write_text(json.dumps(rows,indent=2)); print(json.dumps(row),flush=True)
  finally:
   for p in [b,a]:
    if p:
     p.terminate()
     try:p.wait(timeout=5)
     except subprocess.TimeoutExpired:p.kill();p.wait()
print('ALL RUNS PASS:',all(r['passed'] for r in rows),flush=True)
