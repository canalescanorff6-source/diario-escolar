# 2.0.1

- Corrige migration pendente de ConteudoAula e Escola.brasao_logo.
- Pacote confirmado com mobile-android/ e docs/.

# Changelog

## 2.0.0 — Diário Escolar Pro

### Interface
- Nova identidade visual institucional e responsiva.
- Tema claro/escuro, navegação mobile e PWA configurada.
- Menus de professor e gestão simplificados.
- Novo fluxo unificado **Registrar aula**.
- Remoção de páginas de etapa/checkup/render da experiência do usuário.
- Padronização do nome para **Diário Escolar Pro** e **Assistente Pedagógico**.

### Acadêmico
- Regras de média, atenção e frequência centralizadas na configuração da escola.
- Remoção de média fictícia quando não existem notas.
- Remoção da disciplina automática “Geral” do fluxo normal de lançamento.
- Frequência e conteúdo passam a distinguir múltiplas aulas da mesma disciplina no mesmo dia.
- Índices adicionais nas consultas acadêmicas mais frequentes.

### Segurança
- Segredos e contatos pessoais retirados do código e movidos para variáveis de ambiente.
- Senhas validadas pelo Django, sem senha padrão de gestão.
- Código de autorização da gestão com expiração, limite de tentativas e cooldown de reenvio.
- API Android com token opaco armazenado apenas por hash no servidor.
- Limite de tentativas no login mobile.
- Reforço das permissões professor/turma/disciplina/aluno.
- Proteção de mídia local para evitar exposição anônima de fotos de alunos/professores.

### Estrutura
- Remoção do frontend vazio e de grande quantidade de templates/rotas de desenvolvimento legadas.
- Remoção da fachada de views baseada em wildcard; URLs agora apontam para módulos de domínio.
- Modelos legados de “backup/integradores/indicadores” mantidos apenas para compatibilidade histórica e ocultos do Admin.
- Testes para regras acadêmicas, autorização e API mobile.
- GitHub Actions para qualidade do backend e geração do APK Android.

### Android
- Cliente Android nativo em Java 17 / SDK 36.
- Login do professor, agenda, chamada e conteúdo da aula.
- Cache e fila offline criptografados via Android Keystore/AES-GCM.
- HTTPS obrigatório no aplicativo.
