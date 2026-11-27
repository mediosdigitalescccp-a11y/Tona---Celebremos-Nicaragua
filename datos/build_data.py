# Genera datos.js para el dashboard de Toña · Celebremos Nicaragua.
# Fuentes (hoja "Data Toña 2026", pestañas Data_Celebremos_FB_Ads y Data_Celebremos_GA_Ads):
#   meta_diario.txt, yt_diario.txt, gdn_diario.txt, meta_creativos.json, ga_creativos.json, audiencia.json, plan.py
# Uso: python3 datos/build_data.py
import json, os, sys
from collections import defaultdict
D0 = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D0)
import plan as P

rows = lambda f: [l.split() for l in open(os.path.join(D0, f), encoding='utf-8') if l[:1] == '2']
ETAPA_META = {'E': 'expectativa', 'L': 'lanzamiento', 'L2': 'lanzamiento', 'A': 'lanzamiento', 'C': 'colecciona', 'T': 'colecciona'}
ETAPA_YT = {'E': 'expectativa', 'L': 'lanzamiento', 'A': 'lanzamiento', 'C': 'colecciona'}
CAMP_META = {'E': 'Expectativa', 'L': 'Lanzamiento', 'L2': 'Lanzamiento (conjunto 2)', 'A': 'Alma Pinolera', 'C': 'Colecciona · alcance', 'T': 'Colecciona · tráfico'}
CAMP_YT = {'E': 'Expectativa', 'L': 'Lanzamiento', 'A': 'Alma Pinolera', 'C': 'Colecciona · video'}
LPV_TRF = 60588            # Landing page views de la campaña de tráfico (bloque COLECCIONA, columna FV)
LINK_CLICKS_COLECCIONA = 109292  # Link clicks del bloque COLECCIONA (alcance + tráfico)

diario = []
for f, c, a, i, e, k, cpm, cost, v in rows('meta_diario.txt'):
    diario.append(dict(canal='Meta', etapa=ETAPA_META[c], campana=CAMP_META[c], fecha=f, alcance=int(a), impresiones=int(i), interacciones=int(e), clics=int(k), costo=float(cost), reproducciones=int(v)))
for f, c, u, i, v, cpv, k in rows('yt_diario.txt'):
    diario.append(dict(canal='YouTube', etapa=ETAPA_YT[c], campana=CAMP_YT[c], fecha=f, alcance=int(u), impresiones=int(i), views=int(v), clics=int(k), costo=round(float(cpv) * int(v), 2)))
for f, u, i, k, cost in rows('gdn_diario.txt'):
    diario.append(dict(canal='Display', etapa='colecciona', campana='Colecciona · display', fecha=f, alcance=int(u), impresiones=int(i), clics=int(k), costo=float(cost)))
diario.sort(key=lambda r: (r['fecha'], r['canal']))

A = json.load(open(os.path.join(D0, 'audiencia.json'), encoding='utf-8'))
MC = json.load(open(os.path.join(D0, 'meta_creativos.json'), encoding='utf-8'))
GC = json.load(open(os.path.join(D0, 'ga_creativos.json'), encoding='utf-8'))

# Creativos Meta por etapa
cre_meta = {}
for etapa, rs in MC.items():
    t = defaultdict(lambda: dict(alcance=0, impresiones=0, q25=0, q50=0, q75=0, q100=0, reproducciones=0, dias=set()))
    for r in rs:
        x = t[r[1]]; x['dias'].add(r[0])
        if etapa == 'expectativa':
            q = [int(v or 0) for v in r[2:9]]
            for k, v in zip(('q25', 'q50', 'q75', 'q100', 'reproducciones', 'alcance', 'impresiones'), q): x[k] += v
        else:
            x['alcance'] += int(r[2] or 0); x['impresiones'] += int(r[3] or 0)
    cre_meta[etapa] = sorted([dict(anuncio=k, **{kk: vv for kk, vv in v.items() if kk != 'dias'}, desde=min(v['dias']), hasta=max(v['dias'])) for k, v in t.items()], key=lambda r: -r['impresiones'])

cre_yt = {e: sorted([dict(video=k, views=v[0], desde=v[1], hasta=v[2]) for k, v in GC['yt_' + e].items()], key=lambda r: -r['views']) for e in ('expectativa', 'lanzamiento', 'colecciona')}
cre_gdn = sorted([dict(url=k, impresiones=v[0], clics=v[1], desde=v[2], hasta=v[3]) for k, v in GC['gdn'].items()], key=lambda r: -r['impresiones'])

plan = [dict(n=f['n'], nombre=f['nombre'], ini=f['ini'], fin=f['fin'], presupuesto=f['presupuesto'], objetivo=f['objetivo'], mix=f['mix'], material=f['material'], canales=f['canales']) for f in P.FASES]
ult = max(r['fecha'] for r in diario)
out = dict(actualizado=ult, diario=diario, resumen=A['resumen'], audiencia={k: v for k, v in A.items() if k != 'resumen'},
           creativos=dict(meta=cre_meta, youtube=cre_yt, display=cre_gdn), plan=plan, total_plan=P.TOTAL_CAMPANA,
           extras=dict(lpv=LPV_TRF, link_clicks=LINK_CLICKS_COLECCIONA, lpv_diario=[l.split() for l in open(os.path.join(D0, 'meta_lpv.txt')) if l[:1] == '2']))
open(os.path.join(D0, '..', 'datos.js'), 'w', encoding='utf-8').write('window.TN_DATA = ' + json.dumps(out, ensure_ascii=False) + ';\n')
tot = defaultdict(lambda: [0, 0.0])
for r in diario: tot[(r['canal'], r['etapa'])][0] += r['impresiones']; tot[(r['canal'], r['etapa'])][1] += r['costo']
for k, v in sorted(tot.items()): print(k, v[0], round(v[1], 2))
print('ultimo dia', ult, 'creativos meta', {k: len(v) for k, v in cre_meta.items()}, 'yt', {k: len(v) for k, v in cre_yt.items()}, 'gdn', len(cre_gdn))
