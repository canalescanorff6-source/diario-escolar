@echo off
chcp 65001 > nul
setlocal EnableExtensions

title Gerar serial/key da Gestão - Diário IA Escolar

echo ==========================================================
echo   GERAR SERIAL/KEY DA GESTAO - DIARIO IA ESCOLAR
echo ==========================================================
echo.

REM Se estiver na pasta principal, entra em backend automaticamente.
if exist "backend\manage.py" (
  cd backend
)

if not exist "manage.py" (
  echo ERRO: Nao encontrei o arquivo manage.py.
  echo Coloque este .bat dentro da pasta backend OU na pasta principal do projeto.
  echo Exemplo:
  echo C:\Users\Administrator\Documents\GitHub\diario-escolar\backend
  echo.
  pause
  exit /b 1
)

REM Ativa venv se existir.
if exist ".venv\Scripts\activate.bat" (
  call ".venv\Scripts\activate.bat"
) else if exist "..\.venv\Scripts\activate.bat" (
  call "..\.venv\Scripts\activate.bat"
) else if exist "venv\Scripts\activate.bat" (
  call "venv\Scripts\activate.bat"
) else if exist "..\venv\Scripts\activate.bat" (
  call "..\venv\Scripts\activate.bat"
)

echo IMPORTANTE:
echo - Para gerar a key no banco REAL do site, use a DATABASE_URL do Neon.
echo - Se deixar vazio, vai usar o banco configurado no seu computador.
echo.
set /p NOVA_DATABASE_URL=Cole a DATABASE_URL do Neon ou pressione ENTER para usar a atual: 
if not "%NOVA_DATABASE_URL%"=="" set "DATABASE_URL=%NOVA_DATABASE_URL%"

echo.
set /p GESTOR=Digite o e-mail/usuario da gestao que vai receber a liberacao: 
if "%GESTOR%"=="" (
  echo ERRO: o e-mail/usuario da gestao e obrigatorio.
  pause
  exit /b 1
)

echo.
set /p DIAS=Quantos dias deseja liberar? Exemplo 30, 60, 90: 
if "%DIAS%"=="" set "DIAS=30"

echo.
set /p OBS=Observacao interna opcional. Exemplo nome da escola ou comprovante: 

echo.
echo Deseja enviar a key por e-mail para o e-mail autorizado?
echo O destino padrao e GESTAO_AUTORIZACAO_EMAIL, normalmente thiago01268230@gmail.com.
echo.
set /p ENVIAR_EMAIL=Enviar por e-mail? Digite S para sim ou N para nao: 

if /I "%ENVIAR_EMAIL%"=="S" (
  set "EMAIL_BACKEND=apps.core.email_backends.BrevoEmailBackend"
  if "%EMAIL_TIMEOUT%"=="" set "EMAIL_TIMEOUT=20"

  if "%GESTAO_AUTORIZACAO_EMAIL%"=="" set "GESTAO_AUTORIZACAO_EMAIL=thiago01268230@gmail.com"

  if "%BREVO_API_KEY%"=="" (
    echo.
    set /p BREVO_API_KEY=Cole a BREVO_API_KEY da Brevo, comeca com xkeysib-: 
  )

  if "%BREVO_SENDER_EMAIL%"=="" (
    echo.
    set /p BREVO_SENDER_EMAIL=Digite o e-mail remetente verificado na Brevo: 
  )

  if "%BREVO_SENDER_NAME%"=="" set "BREVO_SENDER_NAME=Diario IA Escolar"
  if "%DEFAULT_FROM_EMAIL%"=="" set "DEFAULT_FROM_EMAIL=Diario IA Escolar <%BREVO_SENDER_EMAIL%>"

  echo.
  echo Gerando serial/key e enviando por e-mail...
  python manage.py gerar_serial_gestao --gestor "%GESTOR%" --dias "%DIAS%" --observacao "%OBS%"
) else (
  echo.
  echo Gerando serial/key somente no terminal, sem enviar e-mail...
  python manage.py gerar_serial_gestao --gestor "%GESTOR%" --dias "%DIAS%" --observacao "%OBS%" --sem-email
)

set "ERRO=%ERRORLEVEL%"
echo.
if "%ERRO%"=="0" (
  echo ==========================================================
  echo   FINALIZADO COM SUCESSO
  echo ==========================================================
  echo.
  echo Se voce usou DATABASE_URL do Neon, a key foi salva no banco online.
  echo A gestao deve colocar a key em:
  echo https://diario-escolar.onrender.com/ativar-acesso-gestao/
) else (
  echo ==========================================================
  echo   DEU ERRO AO GERAR A KEY
  echo ==========================================================
  echo.
  echo Confira se:
  echo - A correcao de licenca ja foi colocada no projeto.
  echo - A DATABASE_URL do Neon esta correta.
  echo - Se escolheu enviar e-mail, a BREVO_API_KEY e o remetente estao corretos.
)

echo.
pause
exit /b %ERRO%
