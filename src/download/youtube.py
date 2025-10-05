import yt_dlp
import os


class YoutubeChannel:
    def __init__(self, path: str):
        self.path = path
        # Criar o diretório se não existir
        self._create_directory()

    def _create_directory(self):
        """Cria o diretório se ele não existir"""
        if not os.path.exists(self.path):
            os.makedirs(self.path, exist_ok=True)
            print(f"Diretório criado: {self.path}")

    def download(self, id: str) -> bool:
        try:
            # URL do vídeo
            url = f'https://www.youtube.com/watch?v={id}'
            
            # Configurações do yt-dlp
            ydl_opts = {
                'outtmpl': os.path.join(self.path, '%(title)s.%(ext)s'),
                'format': 'best[height<=720]',  # Melhor qualidade até 720p
                'noplaylist': True,
                'extract_flat': False,
            }
            
            print(f"Baixando vídeo {id}...")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            print(f"Vídeo {id} baixado com sucesso em {self.path}")
            return True
            
        except Exception as e:
            print(f"Erro ao baixar vídeo {id}: {e}")
            return False