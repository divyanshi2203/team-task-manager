web: gunicorn wsgi:app
release: python -c "from app import create_app, db; app=create_app(); ctx=app.app_context(); ctx.push(); db.create_all(); ctx.pop(); print('DB ready')"
