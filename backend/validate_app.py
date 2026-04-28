import sys
import os
import traceback

def trace(msg):
    print(msg)
    sys.stdout.flush()

try:
    trace("1. flask_sqlalchemy")
    from flask_sqlalchemy import SQLAlchemy
    trace("   OK")

    trace("2. flask_jwt_extended")
    from flask_jwt_extended import JWTManager
    trace("   OK")

    trace("3. flask_cors")
    from flask_cors import CORS
    trace("   OK")

    trace("4. flask_mail")
    from flask_mail import Mail
    trace("   OK")

    trace("5. flask_migrate")
    from flask_migrate import Migrate
    trace("   OK")
    
    trace("6. Import extensions.py")
    from extensions import db
    trace("   OK")

    trace("✅ All extensions imported successfully")
except Exception as e:
    trace(f"❌ Failed: {e}")
    traceback.print_exc()
