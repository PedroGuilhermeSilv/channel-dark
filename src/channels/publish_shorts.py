import os
import glob
import json
import requests
import secrets
import hashlib
import base64
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


@dataclass
class VideoFile:
    """Representa um arquivo de vídeo com seus metadados"""
    file_path: str
    filename: str
    title: str
    size_mb: float
    duration: Optional[int] = None  # em segundos
    resolution: Optional[str] = None
    tags: List[str] = None


@dataclass
class AuthConfig:
    """Configuração de autenticação para plataformas"""
    platform: str
    client_secret: str
    redirect_uri: str
    scope: List[str]
    token_file: str
    client_id: str = None  # Para YouTube
    client_key: str = None  # Para TikTok
    
    def __post_init__(self):
        """Validação pós-inicialização"""
        if self.platform == "youtube" and not self.client_id:
            raise ValueError("YouTube requer client_id")
        if self.platform == "tiktok" and not self.client_key:
            raise ValueError("TikTok requer client_key")


class PlatformAuth:
    """Gerencia autenticação para YouTube"""
    
    def __init__(self, config_path: str = "auth_config.json"):
        self.config_path = config_path
        self.auth_configs = self._load_auth_configs()
    
    def _load_auth_configs(self) -> Dict[str, AuthConfig]:
        """Carrega configurações de autenticação do arquivo JSON"""
        if not os.path.exists(self.config_path):
            return {}
        
        with open(self.config_path, 'r') as f:
            configs = json.load(f)
        
        auth_configs = {}
        for platform, config in configs.items():
            # Normalizar campos para diferentes plataformas
            if platform == "youtube":
                # YouTube usa client_id
                if "client_id" not in config:
                    raise ValueError("Configuração do YouTube deve ter 'client_id'")
            elif platform == "tiktok":
                # TikTok usa client_key
                if "client_key" not in config:
                    raise ValueError("Configuração do TikTok deve ter 'client_key'")
                # Mapear client_key para client_id para compatibilidade
                config["client_id"] = config.get("client_key")
            
            auth_configs[platform] = AuthConfig(**config)
        
        return auth_configs
    
    def authenticate_youtube(self) -> bool:
        """Autentica com YouTube API"""
        try:
            if 'youtube' not in self.auth_configs:
                print("❌ Configuração do YouTube não encontrada")
                return False
            
            config = self.auth_configs['youtube']
            token_file = config.token_file
            
            # Verificar se já existe token válido
            if os.path.exists(token_file):
                try:
                    with open(token_file, 'r') as f:
                        creds_data = json.load(f)
                    
                    # Verificar se é o formato correto
                    if 'token' in creds_data and 'refresh_token' in creds_data:
                        creds = Credentials.from_authorized_user_info(creds_data)
                        
                        if creds.valid:
                            print("✅ Autenticação do YouTube válida")
                            return True
                except Exception as e:
                    print(f"⚠️ Token inválido, fazendo nova autenticação: {e}")
            
            # Fazer nova autenticação
            flow = InstalledAppFlow.from_client_secrets_file(
                f"credentials_{config.platform}.json",
                config.scope
            )
            
            # Para WSL, usar método manual
            print("🔗 Abrindo URL de autenticação...")
            
            # Usar redirect_uri que funciona sem configuração
            flow.redirect_uri = 'http://localhost:8080/callback'
            
            auth_url, _ = flow.authorization_url(prompt='consent')
            print("\n🌐 Abra este link no seu navegador:")
            print(f"   {auth_url}")
            print("\n📋 Após autorizar, copie o código da URL e cole aqui:")
            
            auth_code = input("Código de autorização: ").strip()
            
            # Trocar código por credenciais
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
            
            with open(token_file, 'w') as f:
                json.dump(token_data, f)
            
            print("✅ Autenticação do YouTube concluída")
            return True
            
        except Exception as e:
            print(f"❌ Erro na autenticação do YouTube: {e}")
            return False
    
    def get_youtube_service(self):
        """Retorna serviço autenticado do YouTube"""
        try:
            config = self.auth_configs['youtube']
            token_file = config.token_file
            
            with open(token_file, 'r') as f:
                creds_data = json.load(f)
                
            # Verificar se é o formato correto
            if 'token' in creds_data and 'refresh_token' in creds_data:
                # Formato correto do token
                creds = Credentials.from_authorized_user_info(creds_data)
            else:
                # Formato incorreto, tentar recriar
                print("⚠️ Formato de token incorreto, recriando...")
                return None
            
            return build('youtube', 'v3', credentials=creds)
        except Exception as e:
            print(f"❌ Erro ao obter serviço do YouTube: {e}")
            return None
    
    def _generate_pkce(self) -> tuple[str, str]:
        """Gera code_verifier e code_challenge para PKCE"""
        # Gerar code_verifier (43-128 caracteres)
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        
        # Gerar code_challenge (SHA256 do code_verifier)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        return code_verifier, code_challenge
    
    def authenticate_tiktok(self) -> bool:
        """Autentica com TikTok API usando Login Kit for Web"""
        try:
            if 'tiktok' not in self.auth_configs:
                print("❌ Configuração do TikTok não encontrada")
                return False
            
            config = self.auth_configs['tiktok']
            token_file = config.token_file
            
            # Verificar se já existe token válido
            if os.path.exists(token_file):
                try:
                    with open(token_file, 'r') as f:
                        token_data = json.load(f)
                    
                    # Verificar se o token ainda é válido
                    if self._is_tiktok_token_valid(token_data):
                        print("✅ Autenticação do TikTok válida")
                        return True
                except Exception as e:
                    print(f"⚠️ Token inválido, fazendo nova autenticação: {e}")
            
            # Fazer nova autenticação
            print("🔗 Abrindo URL de autenticação do TikTok...")
            
            # Gerar PKCE
            code_verifier, code_challenge = self._generate_pkce()
            
            # Construir URL de autorização (v2 OAuth API com PKCE)
            auth_url = (
                f"https://www.tiktok.com/v2/auth/authorize/"
                f"?client_key={config.client_key or config.client_id}"
                f"&scope={','.join(config.scope)}"
                f"&response_type=code"
                f"&redirect_uri={config.redirect_uri}"
                f"&code_challenge={code_challenge}"
                f"&code_challenge_method=S256"
            )
            
            print("\n🌐 Abra este link no seu navegador:")
            print(f"   {auth_url}")
            print("\n📋 Após autorizar, copie o código da URL e cole aqui:")
            
            auth_code = input("Código de autorização: ").strip()
            
            # Trocar código por token
            token_data = self._exchange_code_for_token(auth_code, config, code_verifier)
            if not token_data:
                return False
            
            # Salvar token
            with open(token_file, 'w') as f:
                json.dump(token_data, f)
            
            print("✅ Autenticação do TikTok concluída")
            return True
            
        except Exception as e:
            print(f"❌ Erro na autenticação do TikTok: {e}")
            return False
    
    def _is_tiktok_token_valid(self, token_data: Dict) -> bool:
        """Verifica se o token do TikTok ainda é válido"""
        try:
            # Fazer uma requisição simples para verificar se o token funciona
            headers = {
                'Authorization': f"Bearer {token_data['access_token']}"
            }
            
            response = requests.get(
                'https://open.tiktokapis.com/v2/user/info/',
                headers=headers
            )
            
            return response.status_code == 200
        except Exception:
            return False
    
    def _exchange_code_for_token(self, code: str, config: AuthConfig, code_verifier: str) -> Optional[Dict]:
        """Troca código de autorização por token de acesso usando PKCE"""
        try:
            url = 'https://open.tiktokapis.com/v2/oauth/token/'
            
            data = {
                'client_key': config.client_key or config.client_id,
                'client_secret': config.client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': config.redirect_uri,
                'code_verifier': code_verifier
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Cache-Control': 'no-cache'
            }
            
            response = requests.post(url, data=data, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Erro ao trocar código por token: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Erro na requisição de token: {e}")
            return None
    
    def get_tiktok_service(self):
        """Retorna dados de autenticação do TikTok"""
        try:
            config = self.auth_configs['tiktok']
            token_file = config.token_file
            
            with open(token_file, 'r') as f:
                token_data = json.load(f)
            
            # Verificar se o token ainda é válido
            if not self._is_tiktok_token_valid(token_data):
                print("⚠️ Token do TikTok expirado, fazendo refresh...")
                if not self._refresh_tiktok_token(token_data, config):
                    return None
            
            return token_data
        except Exception as e:
            print(f"❌ Erro ao obter dados do TikTok: {e}")
            return None
    
    def _refresh_tiktok_token(self, token_data: Dict, config: AuthConfig) -> bool:
        """Atualiza token do TikTok usando refresh_token"""
        try:
            url = 'https://open.tiktokapis.com/v2/oauth/token/'
            
            data = {
                'client_key': config.client_key or config.client_id,
                'client_secret': config.client_secret,
                'grant_type': 'refresh_token',
                'refresh_token': token_data['refresh_token']
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Cache-Control': 'no-cache'
            }
            
            response = requests.post(url, data=data, headers=headers)
            
            if response.status_code == 200:
                new_token_data = response.json()
                # Salvar novo token
                with open(config.token_file, 'w') as f:
                    json.dump(new_token_data, f)
                print("✅ Token do TikTok atualizado")
                return True
            else:
                print(f"❌ Erro ao atualizar token: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao atualizar token: {e}")
            return False


class PublishShorts:
    """Classe para gerenciar o envio de vídeos shorts"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.supported_formats = ['.mp4', '.mov', '.avi', '.mkv']
        
    def get_video_files(self, channel_name: str) -> List[VideoFile]:
        """Obtém lista de arquivos de vídeo de um canal específico"""
        channel_path = self.base_path / channel_name
        
        if not channel_path.exists():
            print(f"❌ Diretório do canal não encontrado: {channel_path}")
            return []
        
        video_files = []
        
        # Buscar todos os arquivos de vídeo
        for format_ext in self.supported_formats:
            pattern = str(channel_path / f"*{format_ext}")
            files = glob.glob(pattern)
            
            for file_path in files:
                try:
                    file_info = self._get_video_info(file_path)
                    video_files.append(file_info)
                except Exception as e:
                    print(f"⚠️ Erro ao processar {file_path}: {e}")
        
        print(f"📁 Encontrados {len(video_files)} vídeos em {channel_name}")
        return video_files
    
    def _get_video_info(self, file_path: str) -> VideoFile:
        """Extrai informações de um arquivo de vídeo"""
        path_obj = Path(file_path)
        
        # Obter tamanho do arquivo
        size_bytes = path_obj.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        
        # Extrair título do nome do arquivo (remover extensão)
        title = path_obj.stem
        
        # Extrair tags do título (palavras após #)
        tags = []
        if '#' in title:
            parts = title.split('#')
            title = parts[0].strip()
            tags = [tag.strip() for tag in parts[1:] if tag.strip()]
        
        return VideoFile(
            file_path=file_path,
            filename=path_obj.name,
            title=title,
            size_mb=round(size_mb, 2),
            tags=tags
        )
    
    def list_videos(self, channel_name: str) -> None:
        """Lista todos os vídeos de um canal"""
        videos = self.get_video_files(channel_name)
        
        if not videos:
            print(f"❌ Nenhum vídeo encontrado em {channel_name}")
            return
        
        print(f"\n📺 Vídeos encontrados em {channel_name}:")
        print("=" * 60)
        
        for i, video in enumerate(videos, 1):
            print(f"{i:2d}. {video.title}")
            print(f"    📁 Arquivo: {video.filename}")
            print(f"    📏 Tamanho: {video.size_mb} MB")
            if video.tags:
                print(f"    🏷️  Tags: {', '.join(video.tags)}")
            print()
    
    def get_video_by_name(self, channel_name: str, video_name: str) -> Optional[VideoFile]:
        """Busca um vídeo específico pelo nome"""
        videos = self.get_video_files(channel_name)
        
        for video in videos:
            if video_name.lower() in video.title.lower() or video_name.lower() in video.filename.lower():
                return video
        
        return None
    
    def prepare_for_upload(self, video: VideoFile, platform: str = "youtube") -> Dict:
        """Prepara metadados para upload no YouTube"""
        metadata = {
            "title": video.title,
            "description": self._generate_description(video),
            "tags": video.tags or [],
            "file_path": video.file_path,
            "platform": platform
        }
        
        # Configurações específicas do YouTube
        metadata.update({
            "category": "Education",  # Categoria padrão para shorts educativos
            "privacy": "public",
            "shorts": True
        })
        
        return metadata
    
    def _generate_description(self, video: VideoFile) -> str:
        """Gera descrição automática para o vídeo"""
        description = f"🎥 {video.title}\n\n"
        
        if video.tags:
            description += "🏷️ Tags: " + " ".join([f"#{tag}" for tag in video.tags]) + "\n\n"
        
        description += "📺 Conteúdo educativo e curioso!\n"
        description += "👍 Se gostou, deixe seu like!\n"
        description += "🔔 Ative as notificações para não perder novos vídeos!"
        
        return description
    
    def validate_video(self, video: VideoFile) -> Dict[str, bool]:
        """Valida se o vídeo está pronto para upload"""
        validation = {
            "file_exists": os.path.exists(video.file_path),
            "has_title": bool(video.title.strip()),
            "size_ok": video.size_mb > 0 and video.size_mb < 1000,  # Menos de 1GB
            "has_tags": bool(video.tags),
            "valid_format": any(video.filename.lower().endswith(ext) for ext in self.supported_formats)
        }
        
        validation["ready_for_upload"] = all(validation.values())
        return validation
    
    def get_upload_summary(self, channel_name: str) -> Dict:
        """Gera resumo dos vídeos prontos para upload"""
        videos = self.get_video_files(channel_name)
        
        if not videos:
            return {"total": 0, "ready": 0, "issues": []}
        
        ready_count = 0
        issues = []
        
        for video in videos:
            validation = self.validate_video(video)
            if validation["ready_for_upload"]:
                ready_count += 1
            else:
                issues.append({
                    "video": video.title,
                    "problems": [k for k, v in validation.items() if not v and k != "ready_for_upload"]
                })
        
        return {
            "total": len(videos),
            "ready": ready_count,
            "issues": issues,
            "ready_percentage": round((ready_count / len(videos)) * 100, 1)
        }
    
    def upload_to_youtube(self, video: VideoFile, auth: PlatformAuth) -> bool:
        """Faz upload de vídeo para YouTube"""
        try:
            service = auth.get_youtube_service()
            if not service:
                return False
            
            # Preparar metadados
            metadata = self.prepare_for_upload(video, "youtube")
            
            # Criar body da requisição
            body = {
                'snippet': {
                    'title': metadata['title'],
                    'description': metadata['description'],
                    'tags': metadata['tags'],
                    'categoryId': '22'  # People & Blogs
                },
                'status': {
                    'privacyStatus': 'public',
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # Fazer upload
            media = MediaFileUpload(
                video.file_path,
                chunksize=-1,
                resumable=True
            )
            
            print(f"📤 Fazendo upload para YouTube: {video.title}")
            
            request = service.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            response = request.execute()
            
            if response:
                video_id = response['id']
                print(f"✅ Upload concluído! ID: {video_id}")
                print(f"🔗 Link: https://www.youtube.com/watch?v={video_id}")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Erro no upload para YouTube: {e}")
            return False
    
    def upload_to_tiktok(self, video: VideoFile, auth: PlatformAuth) -> bool:
        """Faz upload de vídeo para TikTok usando Content Posting API"""
        try:
            token_data = auth.get_tiktok_service()
            if not token_data:
                return False
            
            # 1. Primeiro, obter informações do criador
            print("🔍 Obtendo informações do criador...")
            creator_info = self._query_creator_info(token_data)
            if not creator_info:
                print("❌ Falha ao obter informações do criador")
                return False
            
            print(f"👤 Criador: {creator_info.get('creator_username', 'N/A')}")
            print(f"📏 Duração máxima: {creator_info.get('max_video_post_duration_sec', 'N/A')}s")
            
            # 2. Preparar metadados
            metadata = self.prepare_for_upload(video, "tiktok")
            
            # 3. Calcular chunks para upload
            video_size_bytes = int(video.size_mb * 1024 * 1024)
            chunk_size = 10000000  # 10MB chunks
            total_chunks = (video_size_bytes + chunk_size - 1) // chunk_size
            
            # 4. Preparar dados do vídeo
            video_data = {
                'post_info': {
                    'title': metadata['title'],
                    'privacy_level': 'MUTUAL_FOLLOW_FRIENDS',  # ou 'SELF_ONLY', 'PUBLIC_TO_EVERYONE'
                    'disable_duet': False,
                    'disable_comment': False,
                    'disable_stitch': False,
                    'video_cover_timestamp_ms': 1000
                },
                'source_info': {
                    'source': 'FILE_UPLOAD',
                    'video_size': video_size_bytes,
                    'chunk_size': chunk_size,
                    'total_chunk_count': total_chunks
                }
            }
            
            print(f"📤 Fazendo upload para TikTok: {video.title}")
            print(f"📊 Tamanho: {video.size_mb}MB, Chunks: {total_chunks}")
            
            # 5. Fazer upload do vídeo
            upload_result = self._upload_video_to_tiktok(video, token_data, video_data)
            
            if upload_result:
                print("✅ Upload para TikTok concluído!")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Erro no upload para TikTok: {e}")
            return False
    
    def _query_creator_info(self, token_data: Dict) -> Optional[Dict]:
        """Obtém informações do criador TikTok"""
        try:
            url = 'https://open.tiktokapis.com/v2/post/publish/creator_info/query/'
            
            headers = {
                'Authorization': f"Bearer {token_data['access_token']}",
                'Content-Type': 'application/json; charset=UTF-8'
            }
            
            response = requests.post(url, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('error', {}).get('code') == 'ok':
                    return result.get('data', {})
                else:
                    print(f"❌ Erro na API: {result.get('error', {}).get('message', 'Erro desconhecido')}")
                    return None
            else:
                print(f"❌ Erro HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao obter informações do criador: {e}")
            return None
    
    def _upload_video_to_tiktok(self, video: VideoFile, token_data: Dict, video_data: Dict) -> bool:
        """Faz o upload real do vídeo para TikTok usando chunks"""
        try:
            # 1. Inicializar upload
            print("🚀 Inicializando upload...")
            init_result = self._init_tiktok_upload(token_data, video_data)
            if not init_result:
                return False
            
            upload_url = init_result.get('upload_url')
            publish_id = init_result.get('publish_id')
            
            if not upload_url or not publish_id:
                print("❌ Falha ao obter URL de upload ou publish_id")
                return False
            
            # 2. Fazer upload em chunks
            print("📤 Fazendo upload em chunks...")
            upload_success = self._upload_video_chunks(video, upload_url, video_data)
            if not upload_success:
                return False
            
            # 3. Finalizar upload
            print("✅ Finalizando upload...")
            return self._finalize_tiktok_upload(token_data, publish_id)
                    
        except Exception as e:
            print(f"❌ Erro no upload do vídeo: {e}")
            return False
    
    def _init_tiktok_upload(self, token_data: Dict, video_data: Dict) -> Optional[Dict]:
        """Inicializa upload no TikTok"""
        try:
            url = 'https://open.tiktokapis.com/v2/post/publish/video/init/'
            
            headers = {
                'Authorization': f"Bearer {token_data['access_token']}",
                'Content-Type': 'application/json; charset=UTF-8'
            }
            
            response = requests.post(url, json=video_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('error', {}).get('code') == 'ok':
                    return result.get('data', {})
                else:
                    print(f"❌ Erro na API: {result.get('error', {}).get('message', 'Erro desconhecido')}")
                    return None
            else:
                print(f"❌ Erro HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao inicializar upload: {e}")
            return None
    
    def _upload_video_chunks(self, video: VideoFile, upload_url: str, video_data: Dict) -> bool:
        """Faz upload do vídeo em chunks"""
        try:
            chunk_size = video_data['source_info']['chunk_size']
            total_chunks = video_data['source_info']['total_chunk_count']
            
            with open(video.file_path, 'rb') as video_file:
                for chunk_index in range(total_chunks):
                    print(f"📤 Enviando chunk {chunk_index + 1}/{total_chunks}")
                    
                    # Ler chunk
                    chunk_data = video_file.read(chunk_size)
                    if not chunk_data:
                        break
                    
                    # Preparar headers para upload
                    headers = {
                        'Content-Type': 'application/octet-stream',
                        'Content-Range': f'bytes {chunk_index * chunk_size}-{chunk_index * chunk_size + len(chunk_data) - 1}/*'
                    }
                    
                    # Fazer upload do chunk
                    response = requests.put(upload_url, data=chunk_data, headers=headers)
                    
                    if response.status_code not in [200, 201, 206]:
                        print(f"❌ Erro no upload do chunk {chunk_index + 1}: {response.status_code}")
                        print(f"   Resposta: {response.text}")
                        return False
                    
                    print(f"✅ Chunk {chunk_index + 1} enviado com sucesso")
            
            return True
                    
        except Exception as e:
            print(f"❌ Erro no upload dos chunks: {e}")
            return False
    
    def _finalize_tiktok_upload(self, token_data: Dict, publish_id: str) -> bool:
        """Finaliza o upload no TikTok"""
        try:
            url = 'https://open.tiktokapis.com/v2/post/publish/video/publish/'
            
            headers = {
                'Authorization': f"Bearer {token_data['access_token']}",
                'Content-Type': 'application/json; charset=UTF-8'
            }
            
            data = {
                'publish_id': publish_id
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('error', {}).get('code') == 'ok':
                    print("✅ Vídeo publicado com sucesso no TikTok!")
                    return True
                else:
                    print(f"❌ Erro na finalização: {result.get('error', {}).get('message', 'Erro desconhecido')}")
                    return False
            else:
                print(f"❌ Erro HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao finalizar upload: {e}")
            return False
    
    def upload_video(self, video: VideoFile, platform: str, auth: PlatformAuth) -> bool:
        """Faz upload de vídeo para a plataforma especificada"""
        if platform == "youtube":
            return self.upload_to_youtube(video, auth)
        elif platform == "tiktok":
            return self.upload_to_tiktok(video, auth)
        else:
            print(f"❌ Plataforma não suportada: {platform}")
            return False