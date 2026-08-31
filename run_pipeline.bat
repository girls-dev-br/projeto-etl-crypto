@echo off
echo Iniciando o Pipeline de Criptomoedas...

cd C:\Users\sarat\OneDrive\Documentos\projeto-etl-crypto

echo Ativando ambiente virtual...
call .venv\Scripts\activate.bat

echo 1. Executando Extracao...
python src\extract\extractor.py

echo 2. Executando Transformacao...
python src\transform\transformer.py

echo Pipeline finalizado com sucesso!