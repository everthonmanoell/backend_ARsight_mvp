"""
Teste do Pipeline via HTTP - 10 imagens (equivalente ao test_pipeline.py)
Envia as imagens para o servidor rodando na Jetson e exibe resultado formatado.

Uso:
    python tests/manual/test_pipeline_http.py
    python tests/manual/test_pipeline_http.py --host 192.168.1.5
    python tests/manual/test_pipeline_http.py --host localhost  # se rodar local
"""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

# ── Argumentos ────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--host", default="192.168.1.5", help="IP ou hostname do servidor")
parser.add_argument("--port", default=8000, type=int)
args = parser.parse_args()

BASE_URL = f"http://{args.host}:{args.port}"

# ── Imagens (mesmo batch do test_pipeline.py) ─────────────────────────────────
BATCH_IMAGES = [
    ("data/illumination/bright_overexposed/bright_image1.jpg", "overexposed"),
    ("data/illumination/bright_overexposed/bright_image2.jpg", "overexposed"),
    ("data/illumination/bright_overexposed/bright_image3.jpg", "overexposed"),
    ("data/illumination/bright_overexposed/bright_image4.jpg", "overexposed"),
    ("data/illumination/dark_underexposed/dark_image1.jpg",    "underexposed"),
    ("data/illumination/dark_underexposed/dark_image2.jpg",    "underexposed"),
    ("data/illumination/dark_underexposed/dark_image3.jpg",    "underexposed"),
    ("data/illumination/normal/normal_image1.jpg",             "adequate"),
    ("data/illumination/normal/normal_image2.jpg",             "acceptable"),
    ("data/illumination/normal/normal_image3.jpg",             "adequate"),
]

def sep(char="-", width=100):
    print(char * width)

# ── Main ──────────────────────────────────────────────────────────────────────
sep("=")
print("TESTE DO PIPELINE VIA HTTP - 10 IMAGENS")
print(f"Servidor: {BASE_URL}")
sep("=")

# 1. Health check
try:
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    h = r.json()
    print(f"\nServidor: {h['status'].upper()}  |  model={h['model']}  device={h['device']}  quant={h['quantization']}\n")
except Exception as e:
    print(f"\n[ERRO] Servidor não respondeu em {BASE_URL}: {e}")
    sys.exit(1)

# 2. Carrega arquivos
print(f"Carregando {len(BATCH_IMAGES)} imagens...")
file_handles = []
files_param  = []
expected     = []
missing      = []

for path_str, label in BATCH_IMAGES:
    p = Path(path_str)
    if not p.exists():
        missing.append(path_str)
        continue
    fh = open(p, "rb")
    file_handles.append(fh)
    files_param.append(("files", (p.name, fh, "image/jpeg")))
    expected.append(label)
    print(f"  [ok] {p.name}")

if missing:
    print(f"\n[AVISO] {len(missing)} imagem(ns) não encontrada(s):")
    for m in missing:
        print(f"  {m}")

if not files_param:
    print("\n[ERRO] Nenhuma imagem disponível. Verifique data/illumination/")
    sys.exit(1)

n = len(files_param)
print(f"\n{n} imagem(ns) prontas — enviando para {BASE_URL}/diagnose/batch ...")

# 3. Envia requisição
t_start = time.perf_counter()
try:
    response = requests.post(
        f"{BASE_URL}/diagnose/batch",
        files=files_param,
        timeout=300,   # Jetson Nano pode demorar alguns minutos no batch
    )
    response.raise_for_status()
except requests.exceptions.Timeout:
    print("\n[ERRO] Timeout — o servidor demorou mais de 5 minutos.")
    sys.exit(1)
except requests.exceptions.HTTPError as e:
    print(f"\n[ERRO] HTTP {response.status_code}: {response.text[:300]}")
    sys.exit(1)
finally:
    for fh in file_handles:
        fh.close()

elapsed_total = time.perf_counter() - t_start
data = response.json()

summary = data.get("summary", {})
frames  = data.get("frames",  [])

# 4. Summary do ambiente
print()
sep()
print("SUMMARY DO AMBIENTE")
sep()
print(f"  Risco geral       : {summary.get('overall_risk','?').upper()}")
print(f"  Condição dominante: {summary.get('dominant_label','?')}")
print(f"  Frames problema   : {summary.get('problem_count','?')}/{n}")
print(f"  Frames normais    : {summary.get('normal_count','?')}/{n}")
explanation = summary.get('explanation', '')
print(f"  Explicação        : {explanation[:120]}{'...' if len(explanation)>120 else ''}")
print(f"  Recomendações     :")
for rec in summary.get("recommendations", []):
    print(f"    - {rec}")
mavg = summary.get("metrics_avg", {})
print(f"  Métricas médias   : luma={mavg.get('mean_luma',0):.1f}  "
      f"uniformidade={mavg.get('uniformity',0):.3f}  "
      f"clip_bright={mavg.get('pct_clipped_bright',0):.3f}  "
      f"clip_dark={mavg.get('pct_clipped_dark',0):.3f}")
slm_time = summary.get("processing_time_s", elapsed_total)
print(f"  Tempo SLM (server): {slm_time:.2f}s   ({slm_time/n*1000:.0f}ms/diagnóstico)")

# 5. Resultados por frame
print()
sep()
print("RESULTADOS POR FRAME")
sep()

correct = 0
for i, frame in enumerate(frames):
    fname     = frame.get("filename", f"frame_{i}")
    predicted = frame.get("metrics", {}).get("illumination_label", "?")
    exp_label = expected[i] if i < len(expected) else "?"
    is_correct = predicted == exp_label
    if is_correct:
        correct += 1

    status_tag = "[PASS]" if frame.get("status") == "pass" else "[FAIL]"
    label_tag  = "[ok]"   if is_correct else "[!!]"
    m = frame.get("metrics", {})

    print(f"\n  [{i+1:02d}] {fname}")
    print(f"       Status    : {status_tag} {frame.get('status','?').upper()}  ({frame.get('risk_level','?')})")
    print(f"       Label     : {label_tag} predito={predicted:<18} esperado={exp_label}")
    print(f"       Métricas  : score={m.get('illumination_score',0):.3f}  luma={m.get('mean_luma',0):.1f}  "
          f"std={m.get('std_luma',0):.1f}  uniformidade={m.get('uniformity',0):.3f}")
    expl = frame.get("explanation", "")
    print(f"       Explicação: {expl[:90]}{'...' if len(expl)>90 else ''}")

# 6. Resumo final
accuracy = correct / n * 100 if n else 0
meta_ok  = (slm_time / n) < 1.0

print()
sep("=")
print("RESUMO")
sep("=")
print(f"\n  Imagens processadas  : {n}")
print(f"  Acurácia de label    : {correct}/{n}  ({accuracy:.1f}%)")
print(f"  Tempo total (HTTP)   : {elapsed_total:.2f}s")
print(f"  Tempo SLM (server)   : {slm_time:.2f}s   ({slm_time/n*1000:.0f}ms/diagnóstico)")
print(f"  Meta < 1s/diagnóst.  : {'[OK] atingida' if meta_ok else '[!!] não atingida'}  ({slm_time/n:.3f}s)")

# 7. Salva JSON
from app.config.config import Config as _Config
env         = _Config().get("environment", "legion")  # 'jetson' ou 'legion'
output_dir  = Path("outputs") / env
output_dir.mkdir(parents=True, exist_ok=True)
output_file = output_dir / f"pipeline_http_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

output = {
    "metadata": {
        "timestamp":    datetime.now().isoformat(),
        "environment":  env,
        "server":       BASE_URL,
        "model":       h.get("model"),
        "device":      h.get("device"),
        "quantization": h.get("quantization"),
        "batch_size":  n,
    },
    "performance": {
        "http_total_s":        round(elapsed_total, 3),
        "slm_total_s":         round(slm_time, 3),
        "slm_per_diagnosis_s": round(slm_time / n, 3),
        "target_met":          meta_ok,
    },
    "statistics": {
        "total":    n,
        "correct":  correct,
        "accuracy": round(accuracy, 2),
    },
    "summary": summary,
    "frames":  frames,
}

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nJSON salvo em: {output_file}")

print()
sep()
print("Preview do JSON (primeiras 40 linhas):")
sep()
with open(output_file, encoding="utf-8") as f:
    for i, line in enumerate(f):
        if i >= 40:
            print("  ...")
            break
        print(line, end="")
print()
sep()
print("\nTeste concluído!")
