web: PRODUCTION=True python manage.py collectstatic --noinput && PRODUCTION=True gunicorn portofolio.wsgi --bind 0.0.0.0:$PORT
