@echo off
title Dashboard SLN RDT - Streamlit

echo ============================================
echo  Dashboard de Producao (m2) - SLN RDT
echo  Responsavel: Fernanda Pacheco
echo ============================================
echo.

REM Comentario: Ir para a pasta do projeto
cd /d C:\fernanda_apps\dashboard_sln_rdt

REM Comentario: Garantir que estamos na pasta certa
echo Diretorio atual:
cd
echo.

REM Comentario: Instalar dependencias (nao falha se ja estiver tudo instalado)
echo Instalando / verificando dependencias...
pip install -r requirements.txt
echo.

REM Comentario: Subir o Streamlit
echo Iniciando o dashboard...
echo.
streamlit run app\app.py

REM Comentario: Manter a janela aberta se algo der errado
echo.
echo O Streamlit foi encerrado.
pause
