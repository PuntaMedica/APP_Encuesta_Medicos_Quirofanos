from flask import Flask, render_template_string, request, send_file, redirect, url_for, session, flash
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'clave-secreta'  # Cámbiala en producción

USERS_FILE = 'usuarios.xlsx'
EXCEL_FILE = 'encuesta.xlsx'

# Si no existe el archivo de usuarios, lo creamos con columnas user y password
if not os.path.exists(USERS_FILE):
    df_users = pd.DataFrame(columns=['user', 'password'])
    df_users.to_excel(USERS_FILE, index=False)
    print(f"Creado {USERS_FILE}. Añade usuarios con sus contraseñas en ese archivo.")

# Plantilla para la página de login
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

# Plantilla HTML de la encuesta con botón de Cerrar sesión
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
        {% else %}
        <form method="POST">
            <!-- aquí va todo tu formulario -->
            <label>NOMBRE (si lo considera):</label>
            <input type="text" name="nombre">

            <label>FECHA:</label>
            <input type="date" name="fecha">

            <label>PROCEDIMIENTO REALIZADO:</label>
            <input type="text" name="procedimiento">

            <label>1. ¿Cómo calificaría el proceso de programación?</label>
            <select name="q1">
                <option value="Malo">Malo</option>
                <option value="Regular">Regular</option>
                <option value="Bueno">Bueno</option>
                <option value="Excelente">Excelente</option>
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
                <option value="Malo">Malo</option>
                <option value="Regular">Regular</option>
                <option value="Bueno">Bueno</option>
                <option value="Excelente">Excelente</option>
            </select>

            <label>6. ¿Cómo podría mejorar el equipo quirúrgico?</label>
            <textarea name="q6"></textarea>

            <label>7. ¿Cómo evalúa las instalaciones y funcionamiento de nuestros quirófanos?</label>
            <select name="q7">
                <option value="Malo">Malo</option>
                <option value="Regular">Regular</option>
                <option value="Bueno">Bueno</option>
                <option value="Excelente">Excelente</option>
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
            <p>Nombre:</p>
            <input type="text" name="prov1_nombre">
            <p>Datos de Contacto:</p>
            <input type="text" name="prov1_contacto">

            <p>Nombre:</p>
            <input type="text" name="prov2_nombre">
            <p>Datos de Contacto:</p>
            <input type="text" name="prov2_contacto">

            <p>Nombre:</p>
            <input type="text" name="prov3_nombre">
            <p>Datos de Contacto:</p>
            <input type="text" name="prov3_contacto">

            <label>12. ¿Tiene algún comentario adicional?</label>
            <textarea name="q12"></textarea>

            <button type="submit">Enviar</button>
        </form>
        {% endif %}
    </div>
</body>
</html>
"""

def check_login(username, password):
    """Verifica credenciales contra usuarios.xlsx"""
    df = pd.read_excel(USERS_FILE, dtype=str)
    return ((df['user'] == username) & (df['password'] == password)).any()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']
        if check_login(user, pwd):
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
        datos = {
            'Fecha de Envío': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'Nombre': request.form.get('nombre'),
            'Fecha': request.form.get('fecha'),
            'Procedimiento': request.form.get('procedimiento'),
            'Q1': request.form.get('q1'),
            'Q2': request.form.get('q2'),
            'Q3': request.form.get('q3'),
            'Q3_motivo': request.form.get('q3_motivo'),
            'Q4': request.form.get('q4'),
            'Q4_motivo': request.form.get('q4_motivo'),
            'Q5': request.form.get('q5'),
            'Q6': request.form.get('q6'),
            'Q7': request.form.get('q7'),
            'Q8': request.form.get('q8'),
            'Q8_motivo': request.form.get('q8_motivo'),
            'Q9': request.form.get('q9'),
            'Q9_motivo': request.form.get('q9_motivo'),
            'Q10': request.form.get('q10'),
            'Proveedor1_Nombre': request.form.get('prov1_nombre'),
            'Proveedor1_Contacto': request.form.get('prov1_contacto'),
            'Proveedor2_Nombre': request.form.get('prov2_nombre'),
            'Proveedor2_Contacto': request.form.get('prov2_contacto'),
            'Proveedor3_Nombre': request.form.get('prov3_nombre'),
            'Proveedor3_Contacto': request.form.get('prov3_contacto'),
            'Q12': request.form.get('q12'),
        }

        if os.path.exists(EXCEL_FILE):
            df = pd.read_excel(EXCEL_FILE)
            df = pd.concat([df, pd.DataFrame([datos])], ignore_index=True)
        else:
            df = pd.DataFrame([datos])
        df.to_excel(EXCEL_FILE, index=False)

        return render_template_string(html_template, enviado=True)

    return render_template_string(html_template, enviado=False)

@app.route('/resultados')
def descargar_resultados():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if os.path.exists(EXCEL_FILE):
        return send_file(EXCEL_FILE, as_attachment=True)
    return "El archivo de resultados aún no existe.", 404

if __name__ == '__main__':
    # En modo desarrollo con recarga automática
    app.run(host='0.0.0.0', port=6300, debug=True)