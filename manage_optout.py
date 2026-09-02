#!/usr/bin/env python3
"""
Script para gerenciar opt-outs de mensagens WhatsApp
Permite adicionar, remover e visualizar números que solicitaram opt-out
"""

import json
from pathlib import Path
from datetime import datetime
from send_messages import WhatsAppMessageSender

def menu():
    """Exibe menu principal"""
    print("\n" + "=" * 60)
    print("🔐 GERENCIADOR DE OPT-OUT")
    print("=" * 60)
    print("1. Visualizar lista de opt-outs")
    print("2. Adicionar número a opt-out")
    print("3. Remover número de opt-out")
    print("4. Verificar se número está em opt-out")
    print("5. Limpar toda lista de opt-out")
    print("6. Importar opt-outs de arquivo CSV")
    print("7. Exportar opt-outs para CSV")
    print("0. Sair")
    print("=" * 60)
    return input("Escolha uma opção: ").strip()

def view_optouts(sender):
    """Visualiza lista de opt-outs"""
    stats = sender.get_optout_stats()
    
    if not stats['total_optout']:
        print("\n✅ Nenhum número em opt-out!")
        return
    
    print("\n" + "=" * 60)
    print(f"📋 LISTA DE OPT-OUT ({stats['total_optout']} números)")
    print("=" * 60)
    
    for i, entry in enumerate(stats['lista'], 1):
        data = entry.get('data_optout', 'N/A')[:10]
        print(f"\n{i}. {entry['numero']}")
        print(f"   Nome: {entry.get('nome', 'N/A')}")
        print(f"   Motivo: {entry.get('motivo', 'N/A')}")
        print(f"   Data: {data}")
    
    print("\n" + "=" * 60)

def add_optout(sender):
    """Adiciona número a opt-out"""
    phone = input("Número de telefone (55DDNNNNNNNNN): ").strip()
    nome = input("Nome (opcional): ").strip() or "N/A"
    motivo = input("Motivo (opcional): ").strip() or "Solicitado pelo usuário"
    
    # Formata o número
    phone_formatted = sender.format_phone_number(phone)
    
    if not phone_formatted:
        print("❌ Número inválido!")
        return
    
    if sender.add_optout(phone_formatted, nome, motivo):
        print(f"✅ {phone_formatted} adicionado a opt-out")
    else:
        print(f"⚠️  {phone_formatted} já estava em opt-out")

def remove_optout(sender):
    """Remove número de opt-out"""
    phone = input("Número de telefone (55DDNNNNNNNNN): ").strip()
    
    phone_formatted = sender.format_phone_number(phone)
    
    if not phone_formatted:
        print("❌ Número inválido!")
        return
    
    sender.remove_optout(phone_formatted)

def check_optout(sender):
    """Verifica se número está em opt-out"""
    phone = input("Número de telefone (55DDNNNNNNNNN): ").strip()
    
    phone_formatted = sender.format_phone_number(phone)
    
    if not phone_formatted:
        print("❌ Número inválido!")
        return
    
    if sender.is_opted_out(phone_formatted):
        print(f"✋ {phone_formatted} ESTÁ em opt-out")
    else:
        print(f"✅ {phone_formatted} NÃO está em opt-out")

def clear_optouts(sender):
    """Limpa toda lista de opt-out"""
    confirm = input("⚠️  Tem certeza? Isso vai apagar TODOS os opt-outs (S/N): ").strip().upper()
    
    if confirm == 'S':
        sender.optout_list = []
        sender.save_optout()
        print("✅ Lista de opt-out limpa!")
    else:
        print("❌ Cancelado")

def import_optouts(sender):
    """Importa opt-outs de arquivo CSV"""
    arquivo = input("Caminho do arquivo CSV: ").strip()
    
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        count = 0
        for line in lines[1:]:  # Pula cabeçalho
            parts = line.strip().split(',')
            if len(parts) >= 2:
                phone = parts[0].strip()
                nome = parts[1].strip()
                
                phone_formatted = sender.format_phone_number(phone)
                if phone_formatted:
                    sender.add_optout(phone_formatted, nome, "Importado")
                    count += 1
        
        print(f"✅ {count} números importados!")
    
    except FileNotFoundError:
        print("❌ Arquivo não encontrado!")
    except Exception as e:
        print(f"❌ Erro: {e}")

def export_optouts(sender):
    """Exporta opt-outs para arquivo CSV"""
    arquivo = input("Nome do arquivo de saída (ex: optout_export.csv): ").strip()
    
    try:
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write("numero,nome,motivo,data_optout\n")
            for entry in sender.optout_list:
                f.write(f"{entry['numero']},{entry['nome']},{entry['motivo']},{entry['data_optout']}\n")
        
        print(f"✅ Exportado para {arquivo}")
    
    except Exception as e:
        print(f"❌ Erro: {e}")

def main():
    """Função principal"""
    sender = WhatsAppMessageSender(
        contacts_file="contacts.json",
        log_file="message_log.json",
        optout_file="optout.json"
    )
    
    while True:
        opcao = menu()
        
        if opcao == "1":
            view_optouts(sender)
        elif opcao == "2":
            add_optout(sender)
        elif opcao == "3":
            remove_optout(sender)
        elif opcao == "4":
            check_optout(sender)
        elif opcao == "5":
            clear_optouts(sender)
        elif opcao == "6":
            import_optouts(sender)
        elif opcao == "7":
            export_optouts(sender)
        elif opcao == "0":
            print("\n👋 Até logo!\n")
            break
        else:
            print("❌ Opção inválida!")

if __name__ == "__main__":
    main()
