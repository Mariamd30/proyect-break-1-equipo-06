# Project Break 1 — RAG Engineering: Deporte Municipal

Asistente RAG sobre instalaciones, tarifas y normas del deporte municipal de Madrid.

## Instalación

~~~bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
~~~

## Indexar el corpus

~~~bash
python main.py --index
~~~

## Preguntar

~~~bash
python main.py --query "¿Cuánto cuesta el abono de piscina?"
python main.py --ask "¿Cuánto cuesta el abono de piscina?"
~~~

## Streamlit

~~~bash
streamlit run app.py
~~~

## Fuentes del corpus

(completar con enlaces y fecha de descarga)
