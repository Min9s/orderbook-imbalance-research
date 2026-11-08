"""README figures only. Read unchanged published aggregates; no model fitting.
Requires a Korean font: Apple SD Gothic Neo, Malgun Gothic or Noto Sans CJK KR.
Run: python assets/readme/generate_figures.py
"""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).parent
MODE='b'
BLUE='#245C91';GRAY='#A8B2BE';INK='#233143'
fonts={f.name for f in font_manager.fontManager.ttflist}
font=next((f for f in ['Apple SD Gothic Neo','AppleGothic','Malgun Gothic','Noto Sans CJK KR'] if f in fonts),None)
if font is None:raise RuntimeError('Install a supported Korean font before generating the README figures')
plt.rcParams.update({'font.family':font,'font.size':16,'axes.unicode_minus':False,'text.color':INK,'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,'savefig.facecolor':'white'})
d=json.loads((ROOT/'results/final_v1/primary_holdout.json').read_text())
rows=[d['horizons'][str(h)] for h in [1,5,10]]
for r in rows:
 assert r['labels']==r['directional']+r['zero']
 for model in ['obi','price_change']:
  m=r['models'][model];c=m['confusion_matrix']
  assert abs((c[0][0]/sum(c[0])+c[1][1]/sum(c[1]))/2-m['balanced_accuracy'])<1e-12
obi=np.array([r['models']['obi']['balanced_accuracy'] for r in rows]);base=np.array([r['models']['price_change']['balanced_accuracy'] for r in rows])
fig,ax=plt.subplots(figsize=(8,3.6 if MODE=='a' else 4.0))
if MODE=='a':
 y=np.arange(3)
 ax.hlines(y,base,obi,color='#D8DEE5',lw=3)
 ax.scatter(base,y,s=70,color=GRAY,zorder=3,label='과거 가격 방향')
 ax.scatter(obi,y,s=90,color=BLUE,zorder=3,label='OBI 모델')
 for i,(o,b) in enumerate(zip(obi,base)):
  ax.text(o+.008,i-.09,f'{o:.3f}',color=BLUE,fontsize=17,weight='bold')
  ax.text(b-.008,i+.23,f'{b:.3f}',color='#5D6977',ha='right',fontsize=15)
 ax.set(yticks=y,yticklabels=['1초','5초','10초'],ylim=(2.5,-.6),xlim=(.45,.84),xticks=[.5,.6,.7,.8])
 ax.set_xlabel('Balanced Accuracy',fontsize=13)
else:
 x=np.arange(3);w=.27
 ax.bar(x-w/2,obi,w,color=BLUE,label='OBI 모델');ax.bar(x+w/2,base,w,color=GRAY,label='과거 가격 방향')
 for i,(o,b) in enumerate(zip(obi,base)):
  ax.text(i-w/2,o+.025,f'{o:.3f}',ha='center',color=BLUE,fontsize=16,weight='bold')
  ax.text(i+w/2,b+.025,f'{b:.3f}',ha='center',color='#5D6977',fontsize=16)
 ax.set(xticks=x,xticklabels=['1초','5초','10초'],ylim=(0,1),yticks=[0,.5,1])
 ax.set_ylabel('Balanced Accuracy',fontsize=13)
 ax.axhline(.5,color='#CCD3DC',lw=.8,ls=':',zorder=0)
for s in ax.spines.values():s.set_visible(False)
ax.tick_params(length=0,pad=8)
h,l=ax.get_legend_handles_labels()
if MODE=='a':h,l=h[::-1],l[::-1]
fig.legend(h,l,loc='upper left',bbox_to_anchor=(.12,.99),ncol=2,frameon=False,fontsize=15)
fig.subplots_adjust(left=.13,right=.97,top=.79,bottom=.19)
fig.savefig(OUT/'performance.png',dpi=200);plt.close(fig)
fig,ax=plt.subplots(figsize=(8,2.9))
y=np.arange(3);change=np.array([r['directional']/r['labels']*100 for r in rows]);flat=100-change
ax.barh(y,change,height=.42,color=BLUE);ax.barh(y,flat,left=change,height=.42,color='#E1E6EC')
for i,(c,f) in enumerate(zip(change,flat)):
 ax.text(c/2,i,f'{c:.1f}%',ha='center',va='center',color='white',fontsize=17,weight='bold')
 ax.text(102,i,f'{f:.1f}%',va='center',color='#5D6977',fontsize=16)
ax.set(yticks=y,yticklabels=['1초','5초','10초'],ylim=(2.5,-.6),xlim=(0,120),xticks=[])
for s in ax.spines.values():s.set_visible(False)
ax.tick_params(length=0,pad=10)
fig.text(.13,.92,'가격 변화',color=BLUE,fontsize=16,weight='bold');fig.text(.82,.92,'무변화',color='#5D6977',fontsize=15)
fig.subplots_adjust(left=.13,right=.97,top=.81,bottom=.12)
fig.savefig(OUT/'coverage.png',dpi=200);plt.close(fig)
print('PASS: BA verified from matrices, label counts verified; two presentation-only figures generated')
