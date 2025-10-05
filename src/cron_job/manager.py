import os
import time
import schedule
import random
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path

from src.channels.publish_shorts import PublishShorts, PlatformAuth


class VideoManager:
    """Gerenciador automático de upload de vídeos"""
    
    def __init__(self, config: dict):
        self.config = config
        self.publisher = PublishShorts(config['base_path'])
        self.auth = PlatformAuth(config['auth_config_path'])
        self.uploaded_videos = self._load_uploaded_list()
        self.last_upload_time = None
        self._authenticated = False
        
    def _load_uploaded_list(self) -> set:
        """Carrega lista de vídeos já enviados"""
        uploaded_file = Path(self.config['base_path']) / 'uploaded_videos.txt'
        if uploaded_file.exists():
            with open(uploaded_file, 'r') as f:
                return set(line.strip() for line in f if line.strip())
        return set()
    
    def _save_uploaded_video(self, video_filename: str):
        """Salva vídeo na lista de enviados"""
        self.uploaded_videos.add(video_filename)
        uploaded_file = Path(self.config['base_path']) / 'uploaded_videos.txt'
        with open(uploaded_file, 'a') as f:
            f.write(f"{video_filename}\n")
    
    def _get_next_video(self, channel_name: str) -> Optional[object]:
        """Seleciona próximo vídeo para upload"""
        videos = self.publisher.get_video_files(channel_name)
        
        if not videos:
            print("❌ Nenhum vídeo disponível")
            return None
        
        # Filtrar vídeos não enviados
        available_videos = [
            video for video in videos 
            if video.filename not in self.uploaded_videos
        ]
        
        if not available_videos:
            print("❌ Todos os vídeos já foram enviados")
            return None
        
        # Selecionar vídeo aleatório ou por ordem
        if self.config.get('random_selection', True):
            return random.choice(available_videos)
        else:
            return available_videos[0]
    
    def _check_upload_interval(self) -> bool:
        """Verifica se é hora de fazer upload"""
        if not self.last_upload_time:
            return True
        
        interval_hours = self.config.get('upload_interval_hours', 24)
        time_since_last = datetime.now() - self.last_upload_time
        
        return time_since_last >= timedelta(hours=interval_hours)
    
    def _should_upload_now(self) -> bool:
        """Verifica se deve fazer upload agora baseado no horário"""
        current_hour = datetime.now().hour
        start_hour = self.config.get('upload_start_hour', 9)
        end_hour = self.config.get('upload_end_hour', 18)
        
        return start_hour <= current_hour <= end_hour
    
    def upload_next_video(self):
        """Faz upload do próximo vídeo"""
        try:
            print(f"\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Verificando upload...")
            
            # Verificar intervalos
            if not self._check_upload_interval():
                print("⏰ Ainda não é hora de fazer upload")
                return
            
            if not self._should_upload_now():
                print("⏰ Fora do horário de upload")
                return
            
            # Selecionar vídeo
            channel_name = self.config['channel_name']
            video = self._get_next_video(channel_name)
            
            if not video:
                return
            
            print(f"🎬 Vídeo selecionado: {video.title}")
            print(f"   📁 Arquivo: {video.filename}")
            print(f"   📏 Tamanho: {video.size_mb} MB")
            
            # Validar vídeo
            validation = self.publisher.validate_video(video)
            if not validation["ready_for_upload"]:
                print("❌ Vídeo não está pronto para upload")
                return
            
            # Verificar autenticação
            if not self.check_authentication():
                print("❌ Falha na autenticação. Execute a configuração inicial.")
                return
            
            # Preparar metadados
            metadata = self.publisher.prepare_for_upload(video, "youtube")
            print(f"📝 Título: {metadata['title']}")
            print(f"📝 Tags: {', '.join(metadata['tags'])}")
            
            # Fazer upload
            print("📤 Iniciando upload...")
            success = self.publisher.upload_video(video, "youtube", self.auth)
            
            if success:
                print("✅ Upload realizado com sucesso!")
                self._save_uploaded_video(video.filename)
                self.last_upload_time = datetime.now()
                
                # Log do upload
                log_entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {video.title} - {video.filename}"
                self._log_upload(log_entry)
            else:
                print("❌ Falha no upload")
                
        except Exception as e:
            print(f"❌ Erro no upload: {e}")
            self._log_error(f"Erro no upload: {e}")
    
    def _log_upload(self, message: str):
        """Registra log de upload"""
        log_file = Path(self.config['base_path']) / 'upload_log.txt'
        with open(log_file, 'a') as f:
            f.write(f"{message}\n")
    
    def _log_error(self, message: str):
        """Registra log de erro"""
        error_file = Path(self.config['base_path']) / 'error_log.txt'
        with open(error_file, 'a') as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
    
    def get_status(self) -> dict:
        """Retorna status do gerenciador"""
        channel_name = self.config['channel_name']
        videos = self.publisher.get_video_files(channel_name)
        available_videos = [
            video for video in videos 
            if video.filename not in self.uploaded_videos
        ]
        
        return {
            'total_videos': len(videos),
            'uploaded_videos': len(self.uploaded_videos),
            'available_videos': len(available_videos),
            'last_upload': self.last_upload_time,
            'next_upload_in': self._get_next_upload_time()
        }
    
    def _get_next_upload_time(self) -> Optional[datetime]:
        """Calcula próxima data de upload"""
        if not self.last_upload_time:
            return datetime.now()
        
        interval_hours = self.config.get('upload_interval_hours', 24)
        return self.last_upload_time + timedelta(hours=interval_hours)
    
    def setup_authentication(self) -> bool:
        """Configura autenticação inicial"""
        print("🔐 Configurando autenticação do YouTube...")
        print("⚠️ Esta etapa é necessária apenas uma vez!")
        
        try:
            success = self.auth.authenticate_youtube()
            if success:
                self._authenticated = True
                print("✅ Autenticação configurada com sucesso!")
                print("💾 Token salvo para uso futuro")
                return True
            else:
                print("❌ Falha na autenticação")
                return False
        except Exception as e:
            print(f"❌ Erro na configuração: {e}")
            return False
    
    def check_authentication(self) -> bool:
        """Verifica se está autenticado"""
        if self._authenticated:
            return True
        
        # Tentar autenticar automaticamente
        try:
            success = self.auth.authenticate_youtube()
            if success:
                self._authenticated = True
                return True
        except Exception:
            pass
        
        return False
    
    def start_scheduler(self):
        """Inicia o agendador automático"""
        print("🚀 Iniciando gerenciador automático de vídeos")
        print(f"📁 Pasta: {self.config['base_path']}")
        print(f"⏰ Intervalo: {self.config.get('upload_interval_hours', 24)} horas")
        print(f"🕐 Horário: {self.config.get('upload_start_hour', 9)}h às {self.config.get('upload_end_hour', 18)}h")
        
        # Agendar uploads
        schedule.every(self.config.get('upload_interval_hours', 24)).hours.do(self.upload_next_video)
        
        # Verificar status inicial
        status = self.get_status()
        print(f"\n📊 Status inicial:")
        print(f"   Total de vídeos: {status['total_videos']}")
        print(f"   Vídeos enviados: {status['uploaded_videos']}")
        print(f"   Vídeos disponíveis: {status['available_videos']}")
        
        # Loop principal
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Verificar a cada minuto
        except KeyboardInterrupt:
            print("\n⏹️ Gerenciador interrompido pelo usuário")
    
    def run_once(self):
        """Executa upload uma única vez"""
        print("🎬 Executando upload único...")
        self.upload_next_video()


def create_config(
    base_path: str,
    channel_name: str,
    upload_interval_hours: int = 24,
    upload_start_hour: int = 9,
    upload_end_hour: int = 18,
    random_selection: bool = True,
    auth_config_path: str = "src/channels/auth_config.json"
) -> dict:
    """Cria configuração para o gerenciador"""
    return {
        'base_path': base_path,
        'channel_name': channel_name,
        'upload_interval_hours': upload_interval_hours,
        'upload_start_hour': upload_start_hour,
        'upload_end_hour': upload_end_hour,
        'random_selection': random_selection,
        'auth_config_path': auth_config_path
    }


def main():
    """Função principal para executar o gerenciador"""
    # Configurações
    config = create_config(
        base_path="/home/guilherme/dev/carnal-dark/db",
        channel_name="nossouniverso00oficial",
        upload_interval_hours=6,  # A cada 6 horas
        upload_start_hour=9,      # Das 9h
        upload_end_hour=18,      # Até 18h
        random_selection=True     # Seleção aleatória
    )
    
    # Criar gerenciador
    manager = VideoManager(config)
    
    # Executar uma vez (para teste)
    manager.run_once()
    
    # Para executar continuamente, descomente a linha abaixo:
    # manager.start_scheduler()


if __name__ == "__main__":
    main()
