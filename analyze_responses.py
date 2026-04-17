#!/usr/bin/env python3
"""
Analyze DialoGPT response quality
Verifica se as respostas estão incompletas ou malformadas
"""

import json
import sys
from pathlib import Path
from collections import Counter

def analyze_responses(json_path):
    """Analisa qualidade das respostas geradas"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("\n" + "╔" + "=" * 78 + "╗")
        print("║" + f"  Response Quality Analysis: {json_path.name}".ljust(79) + "║")
        print("╚" + "=" * 78 + "╝\n")
        
        # Coleta todas as respostas
        all_responses = []
        
        # Individual diagnoses
        if 'diagnoses' in data:
            for i, diag in enumerate(data['diagnoses'], 1):
                if 'slm_explanation' in diag:
                    response = diag['slm_explanation']
                    all_responses.append(('frame', i, response))
        
        # Summary
        if 'summary' in data and 'slm_explanation' in data['summary']:
            response = data['summary']['slm_explanation']
            all_responses.append(('summary', None, response))
        
        if not all_responses:
            print("❌ Nenhuma resposta encontrada no JSON")
            return False
        
        # Análise
        print(f"📊 Total de respostas: {len(all_responses)}\n")
        
        # Estatísticas
        lengths = [len(r[2]) for r in all_responses]
        word_counts = [len(r[2].split()) for r in all_responses]
        
        print(f"📏 Comprimento (caracteres):")
        print(f"   Min:     {min(lengths)} chars")
        print(f"   Max:     {max(lengths)} chars")
        print(f"   Média:   {sum(lengths) / len(lengths):.1f} chars")
        
        print(f"\n📝 Comprimento (palavras):")
        print(f"   Min:     {min(word_counts)} words")
        print(f"   Max:     {max(word_counts)} words")
        print(f"   Média:   {sum(word_counts) / len(word_counts):.1f} words")
        
        # Problemas detectados
        print(f"\n🔍 Problemas Detectados:\n")
        
        problems = []
        
        for resp_type, idx, response in all_responses:
            label = f"Frame {idx}" if resp_type == 'frame' else 'Summary'
            
            # Muito curta
            if len(response) < 20:
                problems.append((label, "MUITO CURTA", response))
                print(f"   ⚠️  [{label}] MUITO CURTA ({len(response)} chars)")
                print(f"       → '{response[:60]}...'")
                print()
            
            # Truncada (termina em meio a palavra)
            if response.endswith((' ', '-', ',')):
                problems.append((label, "TRUNCADA", response))
                print(f"   ⚠️  [{label}] TRUNCADA (termina em: '{response[-5:]}')")
                print()
            
            # Repetida
            if len(response) > 100:
                words = response.split()
                word_freq = Counter(words)
                most_common = word_freq.most_common(1)
                if most_common[0][1] > len(words) * 0.3:  # > 30% de repetição
                    problems.append((label, "REPETIDA", response))
                    print(f"   ⚠️  [{label}] REPETIDA (palavra '{most_common[0][0]}' aparece {most_common[0][1]}x)")
                    print()
            
            # Genérica demais
            generic_phrases = [
                'scene has',
                'lighting is',
                'frame',
                'analysis shows',
                'diagnostic'
            ]
            resp_lower = response.lower()
            generic_count = sum(1 for phrase in generic_phrases if phrase in resp_lower)
            if generic_count > 2:
                problems.append((label, "GENÉRICA", response))
                print(f"   ⚠️  [{label}] GENÉRICA DEMAIS ({generic_count} frases genéricas)")
                print()
        
        # Exemplos de respostas
        print(f"\n📋 Exemplos de Respostas:\n")
        
        for i, (resp_type, idx, response) in enumerate(all_responses[:3]):
            label = f"Frame {idx}" if resp_type == 'frame' else 'Summary'
            print(f"[{label}] ({len(response)} chars, {len(response.split())} words)")
            print(f"  → {response}")
            print()
        
        # Resumo de problemas
        if problems:
            print(f"\n⚠️  RESUMO:")
            print(f"   Total de problemas: {len(problems)}")
            problem_types = Counter(p[1] for p in problems)
            for ptype, count in problem_types.items():
                print(f"   - {ptype}: {count}")
        else:
            print(f"\n✅ Nenhum problema detectado!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao analisar JSON: {e}")
        import traceback
        traceback.print_exc()
        return False

def list_recent_batches(outputs_dir):
    """Lista batches recentes"""
    outputs_dir = Path(outputs_dir)
    if not outputs_dir.exists():
        print(f"❌ Diretório não encontrado: {outputs_dir}")
        return []
    
    result_files = sorted(
        outputs_dir.glob('*_result.json'),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    if not result_files:
        print("❌ Nenhum resultado encontrado")
        return []
    
    print(f"\n📂 Found {len(result_files)} batches:\n")
    for i, f in enumerate(result_files[:10], 1):
        print(f"  [{i}] {f.name}")
    
    return result_files

def main():
    """Menu principal"""
    outputs_dir = Path(__file__).parent / 'outputs'
    
    print("\n╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                   Response Quality Analyzer                               ║")
    print("║                        DialoGPT-small Jetson                              ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    
    result_files = list_recent_batches(outputs_dir)
    
    if not result_files:
        print("\nUsage: python analyze_responses.py <batch_number>")
        print("       Exemplo: python analyze_responses.py 1")
        return
    
    # Se passou argumento
    if len(sys.argv) > 1:
        try:
            idx = int(sys.argv[1]) - 1
            if 0 <= idx < len(result_files):
                analyze_responses(result_files[idx])
            else:
                print(f"❌ Batch #{sys.argv[1]} não encontrado")
        except ValueError:
            print("❌ Argumento deve ser um número")
        return
    
    # Menu interativo
    print("\nOpções:")
    print("  0 - Sair")
    for i in range(1, min(11, len(result_files) + 1)):
        print(f"  {i} - Analisar batch #{i}")
    
    choice = input("\nEscolha um batch (0-10): ").strip()
    
    try:
        choice = int(choice)
        if choice == 0:
            print("✅ Saindo...")
            return
        elif 1 <= choice <= len(result_files):
            analyze_responses(result_files[choice - 1])
        else:
            print(f"❌ Opção inválida")
    except ValueError:
        print("❌ Digite um número válido")

if __name__ == '__main__':
    main()
