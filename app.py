# app.py
from flask import Flask, render_template_string, request, send_file, redirect, url_for, session, flash
import pandas as pd
from datetime import datetime
import os
import pyodbc
from functools import wraps

app = Flask(__name__)
app.secret_key = 'clave-secreta'

# ===================== CONFIGURACIÓN SQL SERVER =====================
SQL_CONN_STR = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=DESKTOP-EO74OCH\\SQLEXPRESS;"
    "Database=punta_medica;"
    "Trusted_Connection=yes;"
    "Encrypt=no;"
    "TrustServerCertificate=yes;"
)

def get_db_connection():
    return pyodbc.connect(SQL_CONN_STR)

# ===================== INICIALIZACIÓN DE TABLA =====================
def init_db_quirofanos():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Tabla específica para Quirófanos
    cursor.execute('''
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='EncuestaQuirofanos' AND xtype='U')
        CREATE TABLE EncuestaQuirofanos (
            ID INT IDENTITY(1,1) PRIMARY KEY,
            FechaEnvio DATETIME,
            Nombre VARCHAR(255),
            FechaEncuesta VARCHAR(100),
            Procedimiento VARCHAR(MAX),
            Q1 VARCHAR(100), Q2 VARCHAR(MAX),
            Q3 VARCHAR(100), Q3_motivo VARCHAR(MAX),
            Q4 VARCHAR(100), Q4_motivo VARCHAR(MAX),
            Q5 VARCHAR(100), Q6 VARCHAR(MAX), Q7 VARCHAR(100),
            Q8 VARCHAR(100), Q8_motivo VARCHAR(MAX),
            Q9 VARCHAR(100), Q9_motivo VARCHAR(MAX),
            Q10 VARCHAR(MAX),
            Prov1_Nombre VARCHAR(255), Prov1_Contacto VARCHAR(255),
            Prov2_Nombre VARCHAR(255), Prov2_Contacto VARCHAR(255),
            Prov3_Nombre VARCHAR(255), Prov3_Contacto VARCHAR(255),
            Q12 VARCHAR(MAX)
        )
    ''')
    conn.commit()
    conn.close()

init_db_quirofanos()

# ===================== TEMPLATES =====================
login_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Login</title>
    <style>
        body { font-family: Arial; background: #f7f7f7; margin: 40px; }
        .login-box { background: white; padding: 30px; max-width: 400px; margin: auto; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        label, input { display: block; width: 100%; margin-bottom: 15px; }
        input { padding: 8px; font-size: 1em; }
        button { padding: 10px 20px; cursor: pointer; }
        .error { color: red; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>Iniciar Sesión</h2>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <div class="error">{{ messages[0] }}</div>
          {% endif %}
        {% endwith %}
        <form method="POST">
            <label>Usuario:</label>
            <input type="text" name="username" required>
            <label>Contraseña:</label>
            <input type="password" name="password" required>
            <button type="submit">Entrar</button>
        </form>
    </div>
</body>
</html>
"""

html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Encuesta de Satisfacción</title>
    <style>
        body { font-family: Arial; margin: 40px; background: #f7f7f7; }
        .container { background: white; padding: 30px; max-width: 800px; margin: auto; box-shadow: 0 0 10px rgba(0,0,0,0.1); position: relative; }
        img { width: 120px; position: absolute; top: 10px; left: 10px; }
        .logout { position: absolute; top: 10px; right: 10px; }
        .logout a { text-decoration: none; color: #333; font-weight: bold; }
        h1 { text-align: center; margin-top: 40px; }
        label, textarea, input, select { display: block; width: 100%; margin-bottom: 15px; }
        select { width: 200px; height: 30px; font-size: 0.9em; }
        textarea { height: 60px; }
        .thankyou { text-align: center; font-size: 1.2em; color: green; margin-top: 20px; }
        button { padding: 15px; background: #007bff; color: white; border: none; cursor: pointer; width: 100%; font-size: 1.1em; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logout">
            <a href="{{ url_for('logout') }}">Cerrar sesión</a>
        </div>
        <img src="/static/logo.png" alt="Logo">
        <h1>ENCUESTA DE SATISFACCIÓN A PERSONAL MÉDICO EN QUIRÓFANOS</h1>
        {% if enviado %}
            <p class="thankyou">¡Gracias por responder la encuesta!</p>
            <p style="text-align:center"><a href="{{ url_for('encuesta') }}">Nueva respuesta</a></p>
        {% else %}
        <form method="POST">
            <label>NOMBRE (si lo considera):</label>
            <input type="text" name="nombre">

            <label>FECHA:</label>
            <input type="date" name="fecha">

            <label>PROCEDIMIENTO REALIZADO:</label>
            <input type="text" name="procedimiento">

            <label>1. ¿Cómo calificaría el proceso de programación?</label>
            <select name="q1">
                <option value="Excelente">Excelente</option>
                <option value="Bueno">Bueno</option>
                <option value="Regular">Regular</option>
                <option value="Malo">Malo</option>
            </select>

            <label>2. ¿Qué modificaría usted de este procedimiento?</label>
            <textarea name="q2"></textarea>

            <label>3. ¿Se le brindó información completa y oportuna, respecto a nuestros servicios disponibles, instalaciones, paquetes y trámites?</label>
            <select name="q3">
                <option value="Si">Sí</option>
                <option value="No">No</option>
            </select>
            <label>Si contestó NO, indique por qué:</label>
            <textarea name="q3_motivo"></textarea>

            <label>4. Al llegar al quirófano y previo al inicio de su cirugía: ¿Se encontraba completo el instrumental, equipo médico e insumos que usted solicitó?</label>
            <select name="q4">
                <option value="Si">Sí</option>
                <option value="No">No</option>
            </select>
            <label>Si contestó NO, indique por qué:</label>
            <textarea name="q4_motivo"></textarea>

            <label>5. ¿Cómo califica el desempeño del equipo quirúrgico (circulante, instrumentista, biomédica, anestesia) durante la realización del procedimiento?</label>
            <select name="q5">
                <option value="Excelente">Excelente</option>
                <option value="Bueno">Bueno</option>
                <option value="Regular">Regular</option>
                <option value="Malo">Malo</option>
            </select>

            <label>6. ¿Cómo podría mejorar el equipo quirúrgico?</label>
            <textarea name="q6"></textarea>

            <label>7. ¿Cómo evalúa las instalaciones y funcionamiento de nuestros quirófanos?</label>
            <select name="q7">
                <option value="Excelente">Excelente</option>
                <option value="Bueno">Bueno</option>
                <option value="Regular">Regular</option>
                <option value="Malo">Malo</option>
            </select>

            <label>8. ¿El trato y cuidados a su paciente fue satisfactorio durante el pre y postoperatorio?</label>
            <select name="q8">
                <option value="Si">Sí</option>
                <option value="No">No</option>
            </select>
            <label>Si contestó NO, indique por qué:</label>
            <textarea name="q8_motivo"></textarea>

            <label>9. Si solicitó apoyo de equipo de diagnóstico como laboratorio o imagenología, ¿Este fue brindado oportunamente?</label>
            <select name="q9">
                <option value="Si">Sí</option>
                <option value="No">No</option>
            </select>
            <label>Si contestó NO, indique por qué:</label>
            <textarea name="q9_motivo"></textarea>

            <label>10. En general, ¿Qué aspecto cree que podríamos mejorar para hacer su experiencia más satisfactoria?</label>
            <textarea name="q10"></textarea>

            <label>11. En su práctica quirúrgica, ¿cuáles proveedores son los que utiliza?</label>
            <p><strong>Proveedor 1:</strong></p>
            <input type="text" name="prov1_nombre" placeholder="Nombre">
            <input type="text" name="prov1_contacto" placeholder="Contacto">

            <p><strong>Proveedor 2:</strong></p>
            <input type="text" name="prov2_nombre" placeholder="Nombre">
            <input type="text" name="prov2_contacto" placeholder="Contacto">

            <p><strong>Proveedor 3:</strong></p>
            <input type="text" name="prov3_nombre" placeholder="Nombre">
            <input type="text" name="prov3_contacto" placeholder="Contacto">

            <label>12. ¿Tiene algún comentario adicional?</label>
            <textarea name="q12"></textarea>

            <button type="submit">Enviar Encuesta</button>
        </form>
        {% endif %}
    </div>
</body>
</html>
"""

# ===================== RUTAS =====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT [user] FROM UsuariosWeb WHERE [user]=? AND [password]=?", (user, pwd))
        row = cursor.fetchone()
        conn.close()

        if row:
            session['logged_in'] = True
            session['username'] = user
            return redirect(url_for('encuesta'))
        else:
            flash('Usuario o contraseña incorrectos.')
    return render_template_string(login_template)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def encuesta():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        datos = (
            datetime.now(),
            request.form.get('nombre'),
            request.form.get('fecha'),
            request.form.get('procedimiento'),
            request.form.get('q1'),
            request.form.get('q2'),
            request.form.get('q3'),
            request.form.get('q3_motivo'),
            request.form.get('q4'),
            request.form.get('q4_motivo'),
            request.form.get('q5'),
            request.form.get('q6'),
            request.form.get('q7'),
            request.form.get('q8'),
            request.form.get('q8_motivo'),
            request.form.get('q9'),
            request.form.get('q9_motivo'),
            request.form.get('q10'),
            request.form.get('prov1_nombre'),
            request.form.get('prov1_contacto'),
            request.form.get('prov2_nombre'),
            request.form.get('prov2_contacto'),
            request.form.get('prov3_nombre'),
            request.form.get('prov3_contacto'),
            request.form.get('q12')
        )

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO EncuestaQuirofanos (
                FechaEnvio, Nombre, FechaEncuesta, Procedimiento, Q1, Q2, Q3, Q3_motivo,
                Q4, Q4_motivo, Q5, Q6, Q7, Q8, Q8_motivo, Q9, Q9_motivo, Q10,
                Prov1_Nombre, Prov1_Contacto, Prov2_Nombre, Prov2_Contacto,
                Prov3_Nombre, Prov3_Contacto, Q12
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, datos)
        conn.commit()
        conn.close()

        return render_template_string(html_template, enviado=True)

    return render_template_string(html_template, enviado=False)

@app.route('/resultados')
def descargar_resultados():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    df = pd.read_sql("SELECT * FROM EncuestaQuirofanos", conn)
    conn.close()
    
    if df.empty:
        return "No hay resultados registrados aún.", 404

    reporte_file = 'reporte_quirofanos.xlsx'
    df.to_excel(reporte_file, index=False)
    return send_file(reporte_file, as_attachment=True)

if __name__ == '__main__':
    # Ejecución en puerto 6300 según original
    app.run(host='0.0.0.0', port=6300, debug=True)