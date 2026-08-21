# Aplicativo Android

O aplicativo em `mobile-android/` é nativo, usa Java 17 e Android SDK 36. Ele consome `/api/v1/` do mesmo Django do website.

## Configurar URL da API

```bash
cd mobile-android
gradle :app:assembleDebug -PDIARIO_API_BASE_URL=https://seu-dominio.com/
```

No GitHub, crie uma **Repository Variable** chamada `DIARIO_API_BASE_URL`.

## Segurança local

- O token bruto da API não é salvo no servidor; o backend persiste apenas SHA-256.
- No aparelho, token, cache e fila offline são criptografados com Android Keystore + AES/GCM.
- `usesCleartextTraffic=false`: a URL de produção deve usar HTTPS.
- Backup automático do app está desativado para evitar copiar a sessão para serviços externos.

## Offline

Após pelo menos uma sincronização online, o app guarda de forma criptografada a agenda e os alunos necessários para a chamada. Lançamentos feitos sem internet entram em uma fila local e são enviados quando o painel volta a ter conexão.

A API usa `update_or_create` para frequência/conteúdo por data e número da aula, reduzindo risco de duplicação quando uma requisição precisa ser repetida.

## APK

O workflow `Android APK` gera `app-debug.apk`. Para publicar na Google Play, crie uma assinatura de release fora do repositório e produza um AAB assinado; nunca faça commit do keystore ou das senhas de assinatura.
