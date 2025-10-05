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


def setup_authentication(manager: VideoManager) -> bool:
    """Configura autenticação do YouTube"""
    print("\n🔐 Configuração de Autenticação")
    print("=" * 40)
    print("⚠️ Esta etapa é necessária apenas uma vez!")
    print("📋 Você precisará:")
    print("   1. Abrir uma URL no navegador")
    print("   2. Fazer login com sua conta Google")
    print("   3. Autorizar o acesso")
    print("   4. Copiar o código de autorização")
    
    print("\n💡 Digite 's' para SIM ou 'n' para NÃO")
    proceed = input("Deseja continuar com a autenticação? (s/n): ").lower().strip()
    if proceed not in ['s', 'sim', 'y', 'yes']:
        print("❌ Autenticação cancelada")
        return False
    
    print("\n🔗 Iniciando processo de autenticação...")
    
    try:
        # Importar as classes necessárias
        from google_auth_oauthlib.flow import InstalledAppFlow
        import json
        
        # Configurar flow
        config = manager.auth.auth_configs['youtube']
        flow = InstalledAppFlow.from_client_secrets_file(
            f"credentials_{config.platform}.json",
            config.scope
        )
        flow.redirect_uri = 'http://localhost:8080/callback'
        
        # Gerar URL de autorização
        auth_url, _ = flow.authorization_url(prompt='consent')
        
        print(f"\n🌐 Abra este link no seu navegador:")
        print(f"   {auth_url}")
        print(f"\n📋 Após autorizar, copie o código da URL e cole aqui:")
        
        # Capturar código do usuário
        auth_code = input("Código de autorização: ").strip()
        
        if not auth_code:
            print("❌ Código não fornecido")
            return False
        
        # Trocar código por credenciais
        print("🔄 Processando código...")
        flow.fetch_token(code=auth_code)
        creds = flow.credentials
        
        # Salvar credenciais no formato correto
        token_data = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        
        token_file = config.token_file
        with open(token_file, 'w') as f:
            json.dump(token_data, f)
        
        # Marcar como autenticado
        manager._authenticated = True
        
        print("✅ Autenticação configurada com sucesso!")
        print("💾 Token salvo para uso futuro")
        return True
        
    except Exception as e:
        print(f"❌ Erro na autenticação: {e}")
        return False


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
    print(f"   🔐 Autenticado: {'✅ Sim' if manager._authenticated else '❌ Não'}")


def main():
    """Função principal"""
    print("🎬 Gerenciador Automático de Vídeos")
    print("=" * 40)
    
    manager = None
    
    while True:
        print("\n📋 Opções:")
        print("1. Configurar sistema")
        print("2. Configurar autenticação")
        print("3. Executar upload único")
        print("4. Iniciar modo automático")
        print("5. Ver status")
        print("6. Sair")
        
        choice = input("\nEscolha uma opção (1-6): ").strip()
        
        if choice == "1":
            config = setup_config()
            manager = VideoManager(config)
            print("✅ Configuração salva!")
            
        elif choice == "2":
            if manager is None:
                print("❌ Configure o sistema primeiro (opção 1)")
                continue
            
            if setup_authentication(manager):
                print("🎉 Sistema totalmente configurado!")
            else:
                print("⚠️ Sistema configurado, mas sem autenticação")
                
        elif choice == "3":
            if manager is None:
                print("❌ Configure o sistema primeiro (opção 1)")
                continue
            
            if not manager._authenticated:
                print("❌ Configure a autenticação primeiro (opção 2)")
                continue
                
            manager.upload_next_video()
                
        elif choice == "4":
            if manager is None:
                print("❌ Configure o sistema primeiro (opção 1)")
                continue
                
            if not manager._authenticated:
                print("❌ Configure a autenticação primeiro (opção 2)")
                continue
                
            try:
                print("🚀 Iniciando modo automático...")
                print("Pressione Ctrl+C para parar")
                manager.start_scheduler()
            except KeyboardInterrupt:
                print("\n⏹️ Modo automático interrompido")
                
        elif choice == "5":
            if manager is None:
                print("❌ Configure o sistema primeiro (opção 1)")
                continue
                
            show_status(manager)
                
        elif choice == "6":
            print("👋 Até logo!")
            break
            
        else:
            print("❌ Opção inválida")


if __name__ == "__main__":
    main()
