#!/usr/bin/env python3
"""
Exemplo de uso da autenticação e upload para TikTok usando Content Posting API
"""

from src.channels.publish_shorts import PublishShorts, PlatformAuth

def main():
    # Inicializar autenticação
    auth = PlatformAuth("auth_config.json")
    
    # Autenticar com TikTok
    print("🔐 Autenticando com TikTok...")
    if not auth.authenticate_tiktok():
        print("❌ Falha na autenticação do TikTok")
        print("💡 Certifique-se de que:")
        print("   - Sua aplicação TikTok tem o scope 'video.publish' aprovado")
        print("   - O usuário autorizou o scope 'video.publish'")
        print("   - As credenciais estão corretas no auth_config.json")
        return
    
    # Inicializar gerenciador de vídeos
    publisher = PublishShorts("/caminho/para/videos")
    
    # Listar vídeos de um canal
    channel_name = "meu_canal"
    print(f"\n📺 Listando vídeos do canal: {channel_name}")
    publisher.list_videos(channel_name)
    
    # Obter resumo dos vídeos
    summary = publisher.get_upload_summary(channel_name)
    print(f"\n📊 Resumo do canal:")
    print(f"   Total de vídeos: {summary['total']}")
    print(f"   Prontos para upload: {summary['ready']}")
    print(f"   Percentual pronto: {summary['ready_percentage']}%")
    
    if summary['issues']:
        print(f"\n⚠️ Problemas encontrados:")
        for issue in summary['issues']:
            print(f"   - {issue['video']}: {', '.join(issue['problems'])}")
    
    # Exemplo de upload de um vídeo específico
    video_name = "meu_video"
    video = publisher.get_video_by_name(channel_name, video_name)
    
    if video:
        print(f"\n📤 Fazendo upload do vídeo: {video.title}")
        
        # Validar vídeo antes do upload
        validation = publisher.validate_video(video)
        if not validation['ready_for_upload']:
            print("❌ Vídeo não está pronto para upload")
            problems = [k for k, v in validation.items() if not v and k != "ready_for_upload"]
            print(f"   Problemas: {', '.join(problems)}")
            return
        
        # Verificar duração máxima (TikTok tem limite de 300s para contas não verificadas)
        if video.duration and video.duration > 300:
            print("⚠️ Aviso: Vídeo com mais de 300s pode ser restrito para contas não verificadas")
        
        # Fazer upload para TikTok usando Content Posting API
        print("🚀 Iniciando upload usando TikTok Content Posting API...")
        success = publisher.upload_video(video, "tiktok", auth)
        
        if success:
            print("✅ Upload concluído com sucesso!")
            print("📱 Verifique seu perfil TikTok para ver o vídeo publicado")
        else:
            print("❌ Falha no upload")
            print("💡 Possíveis causas:")
            print("   - Vídeo muito longo (>300s para contas não verificadas)")
            print("   - Formato não suportado")
            print("   - Problemas de conectividade")
            print("   - Token expirado (tente reautenticar)")
    else:
        print(f"❌ Vídeo '{video_name}' não encontrado")

if __name__ == "__main__":
    main()
