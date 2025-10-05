# Carnal Dark

Uma ferramenta de automação para upload de vídeos para YouTube e TikTok.

## 🚀 Funcionalidades

- **Upload para YouTube**: Automação completa de uploads para YouTube
- **Upload para TikTok**: Suporte à TikTok Content Posting API
- **Gerenciamento de vídeos**: Organização e processamento de arquivos
- **Autenticação segura**: OAuth2 para ambas as plataformas
- **Metadados automáticos**: Extração de títulos e tags dos nomes dos arquivos

## 📋 Pré-requisitos

- Python 3.8+
- Contas nas plataformas (YouTube, TikTok)
- Credenciais de desenvolvedor para ambas as APIs

## 🛠️ Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/carnal-dark.git
cd carnal-dark

# Instale as dependências
pip install -r requirements.txt
```

## ⚙️ Configuração

### 1. YouTube API
1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um projeto e habilite a YouTube Data API v3
3. Crie credenciais OAuth2
4. Baixe o arquivo `credentials_youtube.json`

### 2. TikTok API
1. Acesse [TikTok for Developers](https://developers.tiktok.com/)
2. Crie uma aplicação
3. Habilite Content Posting API
4. Configure redirect URI: `https://localhost:8080/callback`

### 3. Configuração do Sistema
```bash
# Copie o arquivo de configuração
cp auth_config.json.example auth_config.json

# Edite com suas credenciais
nano auth_config.json
```

## 🚀 Uso

### Upload para YouTube
```python
from src.channels.publish_shorts import PublishShorts, PlatformAuth

# Autenticar
auth = PlatformAuth("auth_config.json")
auth.authenticate_youtube()

# Fazer upload
publisher = PublishShorts("/caminho/para/videos")
publisher.upload_video(video, "youtube", auth)
```

### Upload para TikTok
```python
# Autenticar
auth.authenticate_tiktok()

# Fazer upload
publisher.upload_video(video, "tiktok", auth)
```

## 📁 Estrutura de Arquivos

```
videos/
├── meu_canal/
│   ├── video1.mp4
│   ├── video2#tag1#tag2.mp4
│   └── video3#educativo.mp4
```

## 🔒 Segurança

- **Tokens locais**: Todos os tokens são armazenados localmente
- **Credenciais seguras**: Nunca compartilhe suas credenciais
- **HTTPS obrigatório**: TikTok requer HTTPS para redirect URIs

## 📚 Documentação

- [Configuração do YouTube](YOUTUBE_SETUP.md)
- [Configuração do TikTok](TIKTOK_SETUP.md)
- [Exemplo de uso](example_tiktok_usage.py)

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## ⚠️ Aviso Legal

- **Termos de Serviço**: [TERMS_OF_SERVICE.md](TERMS_OF_SERVICE.md)
- **Política de Privacidade**: [PRIVACY_POLICY.md](PRIVACY_POLICY.md)
- **Conformidade**: Respeite os termos das plataformas de destino

## 🆘 Suporte

- **Issues**: [GitHub Issues](https://github.com/seu-usuario/carnal-dark/issues)
- **Documentação**: Consulte a documentação do projeto
- **Comunidade**: Participe das discussões

## 🔄 Changelog

### v1.0.0
- Upload para YouTube
- Upload para TikTok
- Autenticação OAuth2
- Gerenciamento de vídeos

## 📞 Contato

- **GitHub**: [@seu-usuario](https://github.com/seu-usuario)
- **Email**: seu-email@exemplo.com
- **Projeto**: [carnal-dark](https://github.com/seu-usuario/carnal-dark)

---

**⚠️ Importante**: Este software é fornecido para fins educacionais e de automação pessoal. Use com responsabilidade e respeite os termos de serviço das plataformas.
