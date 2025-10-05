
import requests
import json
import re
from typing import List, Set
from dataclasses import dataclass


@dataclass
class ListShorts:
    channel_id: str
    video_ids: List[str]
    total_videos: int




class ChannelExternal:
    def __init__(self, channel_id: str):
        self.channel_id = channel_id

    def get_shorts(self) -> ListShorts:
        try:
            # Fazer requisição para a página de shorts do canal
            response = requests.get(f"https://www.youtube.com/{self.channel_id}/shorts")
            
            # Verificar se a resposta é válida
            if response.status_code != 200:
                return {"error": f"HTTP {response.status_code}: {response.reason}"}
            
            # Verificar se a resposta tem conteúdo
            if not response.text.strip():
                return {"error": "Resposta vazia da API"}

            video_ids = self._extract_video_ids(response.text)
            
            return ListShorts(channel_id=self.channel_id, video_ids=video_ids, total_videos=len(video_ids))
                
        except requests.exceptions.RequestException as e:
            return {"error": f"Erro na requisição: {str(e)}"}
        except Exception as e:
            return {"error": f"Erro inesperado: {str(e)}"}

    def _extract_video_ids(self, html_content: str) -> List[str]:
        """Extrai todos os videoId do HTML do YouTube"""
        # Padrão regex para encontrar "videoId": "ID_DO_VIDEO"
        pattern = r'"videoId":\s*"([^"]+)"'
        matches = re.findall(pattern, html_content)
        
        # Remove duplicatas mantendo a ordem
        unique_video_ids = []
        seen = set()
        for video_id in matches:
            if video_id not in seen:
                unique_video_ids.append(video_id)
                seen.add(video_id)
        
        return unique_video_ids

