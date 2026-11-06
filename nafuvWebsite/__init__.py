# MySQL (cPanel hosting) goes through PyMySQL, which needs no compilation.
# On a server using PostgreSQL or SQLite, PyMySQL is simply not needed.
try:
    import pymysql

    pymysql.install_as_MySQLdb()
except ImportError:  # pragma: no cover
    pass
