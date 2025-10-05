#!/usr/bin/env python3
"""
Configurador do Gerenciador de Vídeos
Interface simples para configurar e executar o sistema automático
"""

from src.cron_job.manager import VideoManager, create_config
import os


def setup_config():
    """Configura o sistema interativamente"""
    print("🎬 Configurador do Gerenciador de Vídeos")
    print("=" * 50)
    
    # Pasta dos vídeos
    print("\n📁 Configuração da pasta:")
    base_path = input("Pasta dos vídeos (padrão: /home/guilherme/dev/carnal-dark/db): ").strip()
    if not base_path:
        base_path = "/home/guilherme/dev/carnal-dark/db"
    
    # Nome do canal
    print("\n📺 Configuração do canal:")
    channel_name = input("Nome do canal (padrão: nossouniverso00oficial): ").strip()
    if not channel_name:
        channel_name = "nossouniverso00oficial"
    
    # Intervalo de upload
    print("\n⏰ Configuração de tempo:")
    try:
        interval_hours = int(input("Intervalo entre uploads em horas (padrão: 6): ") or "6")
    except ValueError:
        interval_hours = 6
    
    # Horário de funcionamento
    try:
        start_hour = int(input("Horário de início (padrão: 9): ") or "9")
        end_hour = int(input("Horário de fim (padrão: 18): ") or "18")
    except ValueError:
        start_hour, end_hour = 9, 18
    
    # Seleção de vídeos
    print("\n🎲 Configuração de seleção:")
    random_choice = input("Seleção aleatória de vídeos? (s/N): ").lower().strip()
    random_selection = random_choice == 's'
    
    # Criar configuração
    config = create_config(
        base_path=base_path,
        channel_name=channel_name,
        upload_interval_hours=interval_hours,
        upload_start_hour=start_hour,
        upload_end_hour=end_hour,
        random_selection=random_selection
    )
    
    return config


def show_status(manager: VideoManager):
    """Mostra status do gerenciador"""
    status = manager.get_status()
    
    print("\n📊 Status do Sistema:")
    print(f"   📁 Pasta: {manager.config['base_path']}")
    print(f"   📺 Canal: {manager.config['channel_name']}")
    print(f"   📹 Total de vídeos: {status['total_videos']}")
    print(f"   ✅ Vídeos enviados: {status['uploaded_videos']}")
    print(f"   ⏳ Vídeos disponíveis: {status['available_videos']}")
    print(f"   ⏰ Último upload: {status['last_upload'] or 'Nunca'}")
    print(f"   🔄 Próximo upload: {status['next_upload_in']}")


def main():
    """Função principal"""
    print("🎬 Gerenciador Automático de Vídeos")
    print("=" * 40)
    
    while True:
        print("\n📋 Opções:")
        print("1. Configurar sistema")
        print("2. Executar upload único")
        print("3. Iniciar modo automático")
        print("4. Ver status")
        print("5. Sair")
        
        choice = input("\nEscolha uma opção (1-5): ").strip()
        
        if choice == "1":
            config = setup_config()
            manager = VideoManager(config)
            print("✅ Configuração salva!")
            
        elif choice == "2":
            try:
                manager.upload_next_video()
            except NameError:
                print("❌ Configure o sistema primeiro (opção 1)")
                
        elif choice == "3":
            try:
                print("🚀 Iniciando modo automático...")
                print("Pressione Ctrl+C para parar")
                manager.start_scheduler()
            except NameError:
                print("❌ Configure o sistema primeiro (opção 1)")
            except KeyboardInterrupt:
                print("\n⏹️ Modo automático interrompido")
                
        elif choice == "4":
            try:
                show_status(manager)
            except NameError:
                print("❌ Configure o sistema primeiro (opção 1)")
                
        elif choice == "5":
            print("👋 Até logo!")
            break
            
        else:
            print("❌ Opção inválida")


if __name__ == "__main__":
    main()
