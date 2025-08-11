from app import app
from models.models import db
import mysql.connector
from config import Config


def test_mysql_connection():
    """Kiểm tra kết nối MySQL trực tiếp"""
    print("1. Testing direct MySQL connection...")
    try:
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )

        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"   ✅ MySQL connection successful!")
            print(f"   📋 MySQL version: {version[0]}")
            print(f"   🏠 Host: {Config.DB_HOST}")
            print(f"   👤 User: {Config.DB_USER}")
            print(f"   🗃️  Database: {Config.DB_NAME}")
            cursor.close()
            connection.close()
            return True

    except mysql.connector.Error as e:
        print(f"   ❌ MySQL connection failed: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False


def test_flask_sqlalchemy_connection():
    """Kiểm tra kết nối qua Flask-SQLAlchemy"""
    print("\n2. Testing Flask-SQLAlchemy connection...")
    try:
        with app.app_context():
            # Thử execute một query đơn giản
            result = db.session.execute(db.text("SELECT 1 as test")).fetchone()
            print(f"   ✅ SQLAlchemy connection successful!")
            print(f"   📊 Test query result: {result[0]}")

            # Kiểm tra database URI
            print(f"   🔗 Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
            return True

    except Exception as e:
        print(f"   ❌ SQLAlchemy connection failed: {e}")
        return False


def check_database_exists():
    """Kiểm tra database có tồn tại không"""
    print("\n3. Checking if database exists...")
    try:
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )

        cursor = connection.cursor()
        cursor.execute("SHOW DATABASES LIKE %s", (Config.DB_NAME,))
        result = cursor.fetchone()

        if result:
            print(f"   ✅ Database '{Config.DB_NAME}' exists!")
        else:
            print(f"   ❌ Database '{Config.DB_NAME}' does not exist!")
            print(f"   💡 Create it with: CREATE DATABASE {Config.DB_NAME};")

        cursor.close()
        connection.close()
        return bool(result)

    except Exception as e:
        print(f"   ❌ Error checking database: {e}")
        return False


def check_tables():
    """Kiểm tra các bảng trong database"""
    print("\n4. Checking tables...")
    try:
        with app.app_context():
            # Lấy danh sách bảng
            result = db.session.execute(db.text("SHOW TABLES")).fetchall()

            if result:
                print(f"   ✅ Found {len(result)} tables:")
                for table in result:
                    print(f"      - {table[0]}")
            else:
                print("   ⚠️  No tables found!")
                print("   💡 Run db.create_all() to create tables")

            return len(result) > 0

    except Exception as e:
        print(f"   ❌ Error checking tables: {e}")
        return False


def main():
    print("🔍 Database Connection Test")
    print("=" * 50)

    # Test từng bước
    mysql_ok = test_mysql_connection()

    if mysql_ok:
        db_exists = check_database_exists()
        sqlalchemy_ok = test_flask_sqlalchemy_connection()

        if sqlalchemy_ok:
            tables_exist = check_tables()

            print("\n" + "=" * 50)
            print("📋 SUMMARY:")
            print(f"   MySQL Connection: {'✅' if mysql_ok else '❌'}")
            print(f"   Database Exists: {'✅' if db_exists else '❌'}")
            print(f"   SQLAlchemy Connection: {'✅' if sqlalchemy_ok else '❌'}")
            print(f"   Tables Created: {'✅' if tables_exist else '❌'}")

            if all([mysql_ok, db_exists, sqlalchemy_ok]):
                print("\n🎉 Database connection is working properly!")
                if not tables_exist:
                    print("💡 Next step: Create tables with db.create_all()")
            else:
                print("\n⚠️  Some issues found. Check the details above.")
        else:
            print("\n❌ SQLAlchemy connection failed!")
    else:
        print("\n❌ Basic MySQL connection failed!")
        print("\n🛠️  TROUBLESHOOTING:")
        print("1. Make sure MySQL server is running")
        print("2. Check username/password in config.py")
        print("3. Verify database exists")
        print("4. Check if mysql-connector-python is installed:")
        print("   pip install mysql-connector-python")


if __name__ == '__main__':
    main()
