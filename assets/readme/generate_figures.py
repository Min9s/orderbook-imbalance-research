"""Presentation-only figures from unchanged published aggregate evidence.

Run: python assets/readme/generate_figures.py
Requires Matplotlib and a Korean font (Apple SD Gothic Neo / AppleGothic /
Malgun Gothic / Noto Sans CJK KR). Never fits a model or writes experiment files.
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
INK,BLUE,MUTED,LINE='#233143','#245C91','#647180','#CBD5DF'


def main():
    available={f.name for f in font_manager.fontManager.ttflist}
    font=next((f for f in ['Apple SD Gothic Neo','AppleGothic','Malgun Gothic','Noto Sans CJK KR'] if f in available),None)
    if font is None:raise RuntimeError('Install a supported Korean font before rendering the figures')
    plt.rcParams.update({'font.family':font,'font.size':17,'axes.unicode_minus':False,'text.color':INK,'axes.labelcolor':INK,'xtick.color':MUTED,'ytick.color':INK,'savefig.facecolor':'white'})
    primary=json.loads((ROOT/'results/final_v1/primary_holdout.json').read_text())
    rows=[primary['horizons'][str(h)] for h in [1,5,10]]
    for row in rows:
        assert row['labels']==row['directional']+row['zero']
        for name in ['obi','price_change']:
            model=row['models'][name];cm=model['confusion_matrix']
            ba=(cm[0][0]/sum(cm[0])+cm[1][1]/sum(cm[1]))/2
            assert abs(ba-model['balanced_accuracy'])<1e-12
    fig,ax=plt.subplots(figsize=(6.8,3.7))
    obi=[r['models']['obi']['balanced_accuracy'] for r in rows]
    base=[r['models']['price_change']['balanced_accuracy'] for r in rows]
    y=np.arange(3)
    ax.hlines(y,base,obi,color=LINE,lw=2)
    ax.scatter(obi,y,s=90,color=BLUE,zorder=3,label='OBI 모델')
    ax.scatter(base,y,s=70,color='#9BA7B5',zorder=3,label='과거 가격 방향')
    for i,(o,b) in enumerate(zip(obi,base)):
        ax.annotate(f'{o:.3f}',(o,i),xytext=(7,-1),textcoords='offset points',va='bottom',color=BLUE,fontsize=20,weight='bold')
        ax.annotate(f'{b:.3f}',(b,i),xytext=(-7,1),textcoords='offset points',va='top',ha='right',color=MUTED,fontsize=18)
    ax.set(yticks=y,yticklabels=['1초','5초','10초'],ylim=(2.5,-.5),xlim=(.45,.87),xticks=[.5,.6,.7,.8])
    ax.tick_params(length=0,pad=10);ax.set_xlabel('Balanced Accuracy',fontsize=13)
    for spine in ax.spines.values():spine.set_visible(False)
    fig.legend(loc='upper left',bbox_to_anchor=(.10,.98),ncol=2,frameon=False,fontsize=18)
    fig.subplots_adjust(left=.13,right=.97,top=.76,bottom=.20)
    fig.savefig(OUT/'final_holdout.png',dpi=200);plt.close(fig)

    row=rows[0];changed=row['directional']/row['labels']*100;flat=row['zero']/row['labels']*100
    assert row['labels']==7034 and row['directional']==4184 and row['zero']==2850
    fig,ax=plt.subplots(figsize=(6.8,2.2))
    ax.barh([0],[changed],height=.42,color=BLUE)
    ax.barh([0],[flat],left=[changed],height=.42,color='#E4E9EF')
    ax.text(changed/2,0,f'{changed:.1f}%',ha='center',va='center',color='white',fontsize=23,weight='bold')
    ax.text(changed+flat/2,0,f'{flat:.1f}%',ha='center',va='center',color=INK,fontsize=23,weight='bold')
    ax.set(xlim=(0,100),ylim=(-.55,.55));ax.set_axis_off()
    fig.text(.06,.84,'가격 변화 4,184개',color=BLUE,fontsize=18,weight='bold')
    fig.text(.64,.84,'무변화 2,850개',color=MUTED,fontsize=17)
    fig.text(.06,.08,'1초 유효 라벨 7,034개 = 100%  /  정확도가 아닌 표본 구성',color=MUTED,fontsize=13)
    fig.subplots_adjust(left=.06,right=.96,top=.75,bottom=.25)
    fig.savefig(OUT/'outcome_coverage.png',dpi=200);plt.close(fig)
    print('PASS: two presentation figures; BA verified from matrices; 1s outcome counts verified.')


if __name__=='__main__':main()
