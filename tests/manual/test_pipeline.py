"""
Teste Manual do Pipeline Completo - True Batch (10 imagens) + Summary
Simula o fluxo real: celular envia 10 frames -> servidor diagnostica em batch -> retorna JSON

Uso:
    python tests/manual/test_pipeline.py

    ou

    com poetry:
    poetry run python tests/manual/test_pipeline.py
"""
import json
import sys
import time
import platform
from datetime import datetime
from pathlib import Path

from PIL import Image
 
sys.path.insert(0, str(Path(__file__).parent.parent.parent)) # Ajuste para acessar app/ a partir de tests/manual/

from app.config.config import Config
from app.pipeline.illumination_pipeline import IlluminationPipeline


def detect_environment() -> str:
    """
    Detecta o ambiente de execução (jetson-nano, jetson-orin, ou desktop-legion)
    
    Returns:
        str: Environment label
    """
    machine = platform.machine()
    
    if machine == "aarch64":
        # É um Jetson, agora diferenciamos entre Nano e Orin
        try:
            with open("/etc/nv_tegra_release", "r") as f:
                release_info = f.read()
                if "R32" in release_info:
                    return "jetson-nano"
                elif "R36" in release_info:
                    return "jetson-orin"
                else:
                    return "jetson"
        except (FileNotFoundError, OSError):
            return "jetson"
    else:
        # Desktop environment
        return "desktop-legion"

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# BANCOS DE IMAGENS POR BATCH - Descomente APENAS UM batch por vez
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Batch 1: 20260315_143220
# BATCH_IMAGES = [
#     ("data/uploads/20260315_143220/frame_00.jpg", "adequate"),
#     ("data/uploads/20260315_143220/frame_01.jpg", "adequate"),
#     ("data/uploads/20260315_143220/frame_02.jpg", "acceptable"),
#     ("data/uploads/20260315_143220/frame_03.jpg", "acceptable"),
#     ("data/uploads/20260315_143220/frame_04.jpg", "acceptable"),
#     ("data/uploads/20260315_143220/frame_05.jpg", "adequate"),
#     ("data/uploads/20260315_143220/frame_06.jpg", "adequate"),
#     ("data/uploads/20260315_143220/frame_07.jpg", "adequate"),
#     ("data/uploads/20260315_143220/frame_08.jpg", "adequate"),
#     ("data/uploads/20260315_143220/frame_09.jpg", "adequate"),
# ]

# Batch 2: 20260315_143447 
# BATCH_IMAGES = [
#     ("data/uploads/20260315_143447/frame_00.jpg", "acceptable"),
#     ("data/uploads/20260315_143447/frame_01.jpg", "acceptable"),
#     ("data/uploads/20260315_143447/frame_02.jpg", "acceptable"),
#     ("data/uploads/20260315_143447/frame_03.jpg", "acceptable"),
#     ("data/uploads/20260315_143447/frame_04.jpg", "acceptable"),
#     ("data/uploads/20260315_143447/frame_05.jpg", "acceptable"),
#     ("data/uploads/20260315_143447/frame_06.jpg", "acceptable"),
#     ("data/uploads/20260315_143447/frame_07.jpg", "underexposed"),
#     ("data/uploads/20260315_143447/frame_08.jpg", "acceptable"),
#     ("data/uploads/20260315_143447/frame_09.jpg", "acceptable"),
# ]

# Batch 3: 20260315_143615 
# BATCH_IMAGES = [
#     ("data/uploads/20260315_143615/frame_00.jpg", "adequate"),
#     ("data/uploads/20260315_143615/frame_01.jpg", "adequate"),
#     ("data/uploads/20260315_143615/frame_02.jpg", "adequate"),
#     ("data/uploads/20260315_143615/frame_03.jpg", "adequate"),
#     ("data/uploads/20260315_143615/frame_04.jpg", "adequate"),
#     ("data/uploads/20260315_143615/frame_05.jpg", "adequate"),
#     ("data/uploads/20260315_143615/frame_06.jpg", "adequate"),
#     ("data/uploads/20260315_143615/frame_07.jpg", "adequate"),
#     ("data/uploads/20260315_143615/frame_08.jpg", "adequate"),
#     ("data/uploads/20260315_143615/frame_09.jpg", "overexposed"),
# ]

# Batch 4: 20260315_143747 
# BATCH_IMAGES = [
#     ("data/uploads/20260315_143747/frame_00.jpg", "adequate"),
#     ("data/uploads/20260315_143747/frame_01.jpg", "adequate"),
#     ("data/uploads/20260315_143747/frame_02.jpg", "adequate"),
#     ("data/uploads/20260315_143747/frame_03.jpg", "adequate"),
#     ("data/uploads/20260315_143747/frame_04.jpg", "adequate"),
#     ("data/uploads/20260315_143747/frame_05.jpg", "adequate"),
#     ("data/uploads/20260315_143747/frame_06.jpg", "adequate"),
#     ("data/uploads/20260315_143747/frame_07.jpg", "adequate"),
#     ("data/uploads/20260315_143747/frame_08.jpg", "adequate"),
#     ("data/uploads/20260315_143747/frame_09.jpg", "acceptable"),
# ]

# Batch 5: 20260315_175638 
BATCH_IMAGES = [
    ("data/uploads/20260315_175638/frame_00.jpg", "underexposed"),
    ("data/uploads/20260315_175638/frame_01.jpg", "underexposed"),
    ("data/uploads/20260315_175638/frame_02.jpg", "underexposed"),
    ("data/uploads/20260315_175638/frame_03.jpg", "underexposed"),
    ("data/uploads/20260315_175638/frame_04.jpg", "underexposed"),
    ("data/uploads/20260315_175638/frame_05.jpg", "underexposed"),
    ("data/uploads/20260315_175638/frame_06.jpg", "underexposed"),
    ("data/uploads/20260315_175638/frame_07.jpg", "underexposed"),
    ("data/uploads/20260315_175638/frame_08.jpg", "underexposed"),
    ("data/uploads/20260315_175638/frame_09.jpg", "underexposed"),
]

# Batch 6: 20260315_180200 
# BATCH_IMAGES = [
#     ("data/uploads/20260315_180200/frame_00.jpg", "adequate"),
#     ("data/uploads/20260315_180200/frame_01.jpg", "adequate"),
#     ("data/uploads/20260315_180200/frame_02.jpg", "adequate"),
#     ("data/uploads/20260315_180200/frame_03.jpg", "adequate"),
#     ("data/uploads/20260315_180200/frame_04.jpg", "adequate"),
#     ("data/uploads/20260315_180200/frame_05.jpg", "adequate"),
#     ("data/uploads/20260315_180200/frame_06.jpg", "underexposed"),
#     ("data/uploads/20260315_180200/frame_07.jpg", "underexposed"),
#     ("data/uploads/20260315_180200/frame_08.jpg", "underexposed"),
#     ("data/uploads/20260315_180200/frame_09.jpg", "underexposed"),
# ]

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# método auxiliar para carregar uma imagem usando PIL, retornando None em caso de erro
def load_image(path: str): 
    """Carrega imagem via PIL - tenta múltiplos caminhos."""
    # Tenta o caminho direto
    if Path(path).exists():
        return Image.open(path)
    
    # Tenta relativo a /app (para Docker)
    app_path = Path("/app") / path
    if app_path.exists():
        return Image.open(app_path)
    
    # Tenta relativo ao diretório de trabalho atual
    cwd_path = Path.cwd() / path
    if cwd_path.exists():
        return Image.open(cwd_path)
    
    return None

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# método auxiliar para imprimir uma linha separadora no console, melhorando a legibilidade dos logs durante o teste
def sep(char="-", width=150): 
    print(char * width)

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def main():

    sep("=")
    print("TESTE DO PIPELINE - TRUE BATCH (10 IMAGENS) + SUMMARY")
    sep("=")

    # Extrai o nome da pasta de batch (if available)
    batch_folder_name = None
    if BATCH_IMAGES:
        first_path = BATCH_IMAGES[0][0]  # Pega o primeiro caminho
        # Extrai o nome da pasta pai se for um upload (ex: data/uploads/20260315_143220/frame_00.jpg)
        if "uploads" in first_path:
            batch_folder_name = Path(first_path).parent.name
    
    # Inicializa pipeline 
    config         = Config()                               # Carrega configurações do arquivo YAML
    model_type     = config.get("models.default", "qwen")   # Obtém tipo de modelo (qwen ou phi) a partir da configuração
    use_4bit       = config.get("models.use_4bit", True)    # Verifica se a quantização 4-bit deve ser usada
    device         = config.get("models.device", "cuda")    # Verifica qual dispositivo deve ser usado para inferência (cuda, cpu, ou auto)

    print(f"\nConfig: model={model_type}  4bit={use_4bit}  device={device}")
    if batch_folder_name:
        print(f"Batch:  {batch_folder_name}") 

    t_init = time.perf_counter() # Inicia contagem de tempo para a inicialização do pipeline

    # Inicializa o pipeline de diagnóstico com as configurações especificadas
    pipeline = IlluminationPipeline(model_type=model_type, use_4bit=use_4bit, device=device) 

    # Carrega o modelo SLM
    pipeline._load_model() 

    print(f"Modelo carregado em {time.perf_counter() - t_init:.1f}s")

    # Carrega imagens
    print(f"\nCarregando {len(BATCH_IMAGES)} imagens...")

    # listas para armazenar as imagens carregadas, os nomes dos arquivos e os rótulos esperados
    images, filenames, expected_labels = [], [], [] 

    # lista para rastrear imagens que não foram encontradas, permitindo identificar problemas com os arquivos de teste antes de executar o pipeline
    missing = [] 

    # iterar sobre as imagens definidas em BATCH_IMAGES, tentando carregar cada uma usando a função load_image; 
    # se a imagem for carregada com sucesso, ela é adicionada à lista de imagens, 
    # caso contrário, seu caminho é adicionado à lista de missing para rastreamento de erros
    for path_str, label in BATCH_IMAGES:
        path = Path(path_str)
        img  = load_image(path_str)
        if img is None:
            missing.append(path_str)
            print(f"  [xx] {path.name} - NOT FOUND at {path_str}")
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

    # FASE 1: PDI
    print()
    sep()
    print("FASE 1 - PDI (visao computacional)")
    sep()

    # Inicia contagem de tempo para a fase de PDI, permitindo medir o tempo gasto na extração de métricas de iluminação para o batch de imagens
    t_pdi = time.perf_counter() 

    # Extrai métricas de iluminação para o batch de imagens, retornando uma lista de dicionários com as métricas calculadas para cada imagem
    pdi_metrics = pipeline.extract_metrics_batch(images) 

    # Calcula o tempo total gasto na fase de PDI, permitindo avaliar a eficiência do pipeline na extração de métricas de iluminação para o batch de imagens
    pdi_elapsed = time.perf_counter() - t_pdi 

    print(f"Metricas extraidas: {n} imagens em {pdi_elapsed*1000:.1f}ms  ({pdi_elapsed/n*1000:.1f}ms/img)\n")

    # Imprime as métricas extraídas para cada imagem, incluindo o rótulo de iluminação previsto, a pontuação de iluminação e a média de brilho, 
    for i, (fname, m) in enumerate(zip(filenames, pdi_metrics)):
        print(f"  [{i+1:02d}] {fname:<35}  label={m['illumination_label']:<18}  "
              f"score={m['illumination']:.3f}  luma={m['mean_luma']:.1f}")

    # FASE 2: SLM batch + summary (N+1 prompts num unico batch)
    print()
    sep()
    print("FASE 2 - SLM (true batch: N diagnosticos + 1 summary)")
    sep()

    # Inicia contagem de tempo para a fase de SLM, permitindo medir o tempo gasto na geração dos diagnósticos e do resumo do ambiente usando o modelo de linguagem
    t_slm = time.perf_counter() 

    # Gera diagnósticos para o batch de métricas e um resumo do ambiente, retornando uma lista de diagnósticos individuais para cada imagem e um dicionário com o resumo geral do ambiente
    diagnoses, summary = pipeline.diagnose_from_metrics_batch_with_summary(pdi_metrics) 

    # Calcula o tempo total gasto na fase de SLM, permitindo avaliar a eficiência do modelo de linguagem na geração dos diagnósticos e do resumo para o batch de imagens
    slm_elapsed = time.perf_counter() - t_slm 

    # Calcula o tempo médio gasto por diagnóstico, permitindo avaliar se a meta de latência de 1 segundo por diagnóstico foi atingida
    per_diag = slm_elapsed / n 

    print(f"{n} diagnosticos + 1 summary gerados em {slm_elapsed:.2f}s  ({per_diag*1000:.0f}ms/diagnostico)")

    # Summary do ambiente
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

    # Resultados por frame
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

    # Estatisticas e performance
    total_elapsed = pdi_elapsed + slm_elapsed
    accuracy      = correct / n * 100

    print()
    sep("=")
    print("RESUMO")
    sep("=")
    print(f"\n  Imagens processadas : {n}")
    print(f"  Acuracia de label   : {correct}/{n}  ({accuracy:.1f}%)")
    print(f"\n  Tempo PDI total     : {pdi_elapsed*1000:.1f}ms  ({pdi_elapsed/n*1000:.1f}ms/img)")
    print(f"  Tempo SLM total     : {slm_elapsed:.2f}s   ({per_diag*1000:.0f}ms/diagnostico)")
    print(f"  Tempo total         : {total_elapsed:.2f}s")
    meta_ok = per_diag < 1.0
    print(f"  Meta < 1s/diagnost. : {'[OK] atingida' if meta_ok else '[!!] nao atingida'}  ({per_diag:.3f}s)")

    # Salva JSON
    env         = detect_environment()  # 'jetson-nano', 'jetson-orin', ou 'desktop-legion'
    output_dir  = Path("outputs") / env
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"pipeline_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    output = {
        "metadata": {
            "timestamp":    datetime.now().isoformat(),
            "environment":  env,
            "model":        model_type,
            "device":       device,
            "quantization": "4-bit" if use_4bit else "fp16/fp32",
            "batch_size":   n,
            "batch_folder": batch_folder_name or "unknown",
        },
        "performance": {
            "pdi_total_ms":        round(pdi_elapsed * 1000, 1),
            "pdi_per_image_ms":    round(pdi_elapsed / n * 1000, 1),
            "slm_total_s":         round(slm_elapsed, 3),
            "slm_per_diagnosis_s": round(per_diag, 3),
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

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()