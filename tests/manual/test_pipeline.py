"""
Teste Manual do Pipeline Completo - True Batch (10 imagens) + Summary
Simula o fluxo real: celular envia 10 frames -> servidor diagnostica em batch -> retorna JSON

Uso:
    python tests/manual/test_pipeline.py
"""
import cv2
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.config.config import Config
from app.pipeline.illumination_pipeline import IlluminationPipeline


# Imagens de teste (4 overexposed + 3 underexposed + 3 normal = 10)
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


def load_image(path: str):
    """Carrega imagem via OpenCV e converte para PIL RGB."""
    img_cv = cv2.imread(path)
    if img_cv is None:
        return None
    return Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))


def sep(char="-", width=80):
    print(char * width)


def main():
    sep("=")
    print("TESTE DO PIPELINE - TRUE BATCH (10 IMAGENS) + SUMMARY")
    sep("=")

    # --- Inicializa pipeline ---
    config         = Config()
    model_type     = config.get("models.default", "qwen")
    use_4bit       = config.get("models.use_4bit", True)
    device         = config.get("models.device", "cuda")
    enable_compile = config.get("models.enable_compile", False)

    print(f"\nConfig: model={model_type}  4bit={use_4bit}  device={device}  compile={enable_compile}")

    t_init = time.perf_counter()
    pipeline = IlluminationPipeline(
        model_type=model_type,
        use_4bit=use_4bit,
        device=device,
        enable_compile=enable_compile,
    )
    pipeline._load_model()
    print(f"Modelo carregado em {time.perf_counter() - t_init:.1f}s")

    # --- Carrega imagens ---
    print(f"\nCarregando {len(BATCH_IMAGES)} imagens...")
    images, filenames, expected_labels = [], [], []
    missing = []

    for path_str, label in BATCH_IMAGES:
        path = Path(path_str)
        img  = load_image(path_str)
        if img is None:
            missing.append(path_str)
        else:
            images.append(img)
            filenames.append(path.name)
            expected_labels.append(label)
            print(f"  [ok] {path.name}")

    if missing:
        print(f"\n[AVISO] {len(missing)} imagem(ns) nao encontrada(s):")
        for m in missing:
            print(f"  {m}")

    if not images:
        print("\n[ERRO] Nenhuma imagem disponivel. Verifique data/illumination/")
        return

    n = len(images)
    print(f"\n{n} imagem(ns) prontas para o batch")

    # --- FASE 1: PDI ---
    print()
    sep()
    print("FASE 1 - PDI (visao computacional)")
    sep()

    t_pdi = time.perf_counter()
    pdi_metrics = pipeline.extract_metrics_batch(images)
    pdi_elapsed = time.perf_counter() - t_pdi

    print(f"Metricas extraidas: {n} imagens em {pdi_elapsed*1000:.1f}ms  ({pdi_elapsed/n*1000:.1f}ms/img)\n")

    for i, (fname, m) in enumerate(zip(filenames, pdi_metrics)):
        print(f"  [{i+1:02d}] {fname:<35}  label={m['illumination_label']:<18}  "
              f"score={m['illumination']:.3f}  luma={m['mean_luma']:.1f}")

    # --- FASE 2: LLM batch + summary (N+1 prompts num unico batch) ---
    print()
    sep()
    print("FASE 2 - SLM / LLM (true batch: N diagnosticos + 1 summary)")
    sep()

    t_llm = time.perf_counter()
    diagnoses, summary = pipeline.diagnose_from_metrics_batch_with_summary(pdi_metrics)
    llm_elapsed = time.perf_counter() - t_llm

    per_diag = llm_elapsed / n
    print(f"{n} diagnosticos + 1 summary gerados em {llm_elapsed:.2f}s  ({per_diag*1000:.0f}ms/diagnostico)")

    # --- Summary do ambiente ---
    print()
    sep()
    print("SUMMARY DO AMBIENTE")
    sep()
    print(f"  Risco geral      : {summary['overall_risk'].upper()}")
    print(f"  Condicao dominante: {summary['dominant_label']}")
    print(f"  Frames problema  : {summary['problem_count']}/{n}")
    print(f"  Frames normais   : {summary['normal_count']}/{n}")
    print(f"  Explicacao       : {summary['explanation'][:120]}...")
    print(f"  Recomendacoes    :")
    for rec in summary.get("recommendations", []):
        print(f"    - {rec}")
    mavg = summary.get("metrics_avg", {})
    print(f"  Metricas medias  : luma={mavg.get('mean_luma', 0):.1f}  "
          f"uniformidade={mavg.get('uniformity', 0):.3f}  "
          f"clip_bright={mavg.get('pct_clipped_bright', 0):.3f}  "
          f"clip_dark={mavg.get('pct_clipped_dark', 0):.3f}")

    # --- Resultados por frame ---
    print()
    sep()
    print("RESULTADOS POR FRAME")
    sep()

    results = []
    correct = 0

    for i, (fname, pdi, diag, expected) in enumerate(
            zip(filenames, pdi_metrics, diagnoses, expected_labels)):

        predicted  = pdi["illumination_label"]
        is_correct = predicted == expected
        if is_correct:
            correct += 1

        status_tag = "[PASS]" if diag["status"] == "pass" else "[FAIL]"
        label_tag  = "[ok]"   if is_correct else "[!!]"

        print(f"\n  [{i+1:02d}] {fname}")
        print(f"       Status   : {status_tag} {diag['status'].upper()}  ({diag['risk_level']})")
        print(f"       Label    : {label_tag} predito={predicted:<18} esperado={expected}")
        print(f"       Metricas : score={pdi['illumination']:.3f}  luma={pdi['mean_luma']:.1f}  "
              f"std={pdi['std_luma']:.1f}  uniformidade={pdi['uniformity']:.3f}")
        print(f"       Explicac.: {diag['explanation'][:90]}...")

        results.append({
            "frame_index":     i,
            "filename":        fname,
            "expected_label":  expected,
            "status":          diag["status"],
            "risk_level":      diag["risk_level"],
            "label_correct":   is_correct,
            "explanation":     diag["explanation"],
            "triggered_rules": diag.get("triggered_rules", []),
            "recommendations": diag.get("recommendations", []),
            "metrics": {
                "illumination_score": round(pdi["illumination"], 4),
                "illumination_label": pdi["illumination_label"],
                "mean_brightness":    round(pdi["mean_luma"] / 255.0, 4),
                "mean_luma":          round(pdi["mean_luma"], 2),
                "std_luma":           round(pdi["std_luma"], 2),
                "uniformity":         round(pdi["uniformity"], 4),
                "pct_clipped_dark":   round(pdi["pct_clipped_dark"], 4),
                "pct_clipped_bright": round(pdi["pct_clipped_bright"], 4),
            },
        })

    # --- Estatisticas ---
    total_elapsed = pdi_elapsed + llm_elapsed
    accuracy      = correct / n * 100

    print()
    sep("=")
    print("RESUMO")
    sep("=")
    print(f"\n  Imagens processadas : {n}")
    print(f"  Acuracia de label   : {correct}/{n}  ({accuracy:.1f}%)")
    print(f"\n  Tempo PDI total     : {pdi_elapsed*1000:.1f}ms  ({pdi_elapsed/n*1000:.1f}ms/img)")
    print(f"  Tempo LLM total     : {llm_elapsed:.2f}s   ({per_diag*1000:.0f}ms/diagnostico)")
    print(f"  Tempo total         : {total_elapsed:.2f}s")
    meta_ok = per_diag < 1.0
    print(f"  Meta < 1s/diagnost. : {'[OK] atingida' if meta_ok else '[!!] nao atingida'}  ({per_diag:.3f}s)")

    # --- Salva JSON ---
    output_dir  = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"pipeline_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    output = {
        "metadata": {
            "timestamp":    datetime.now().isoformat(),
            "model":        model_type,
            "device":       device,
            "quantization": "4-bit" if use_4bit else "fp16/fp32",
            "compile":      enable_compile,
            "batch_size":   n,
        },
        "performance": {
            "pdi_total_ms":        round(pdi_elapsed * 1000, 1),
            "pdi_per_image_ms":    round(pdi_elapsed / n * 1000, 1),
            "llm_total_s":         round(llm_elapsed, 3),
            "llm_per_diagnosis_s": round(per_diag, 3),
            "total_s":             round(total_elapsed, 3),
            "target_met":          meta_ok,
        },
        "statistics": {
            "total":    n,
            "correct":  correct,
            "accuracy": round(accuracy, 2),
        },
        "summary": summary,
        "frames":  results,
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
    print("\nTeste concluido!")


if __name__ == "__main__":
    main()