from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import sqlite3
from fpdf import FPDF
import os
app = Flask(__name__)
DATABASE = 'reparaciones.db'

# Función para crear la tabla si no existe
def create_table():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS equipos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_cliente TEXT NOT NULL,
                telefono_cliente TEXT,
                email_cliente TEXT,
                marca TEXT,
                modelo TEXT,
                tipo TEXT,
                numero_serie TEXT,
                descripcion TEXT,
                estado TEXT DEFAULT 'En revisión',
                empresa_derivadora TEXT,
                novedades TEXT
            )
        ''')
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error al crear la tabla: {e}")
    finally:
        conn.close()

# Ruta principal para mostrar los equipos
@app.route('/')
def index():
    create_table()
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM equipos')
        equipos = cursor.fetchall()
        return render_template('index.html', equipos=equipos)
    except sqlite3.Error as e:
        print(f"Error al obtener equipos: {e}")
        return "Error al obtener equipos", 500
    finally:
        conn.close()

# Ruta para agregar un nuevo equipo
@app.route('/nuevo_equipo', methods=['GET', 'POST'])
def nuevo_equipo():
    create_table()
    if request.method == 'POST':
        try:
            nombre_cliente = request.form['nombre_cliente']
            telefono_cliente = request.form['telefono_cliente']
            email_cliente = request.form['email_cliente']
            marca = request.form['marca']
            modelo = request.form['modelo']
            tipo = request.form['tipo']
            numero_serie = request.form['numero_serie']
            descripcion = request.form['descripcion']
            empresa_derivadora = request.form['empresa_derivadora']
            
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute(''' 
                INSERT INTO equipos (nombre_cliente, telefono_cliente, email_cliente, marca, modelo, tipo, numero_serie, descripcion, empresa_derivadora)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (nombre_cliente, telefono_cliente, email_cliente, marca, modelo, tipo, numero_serie, descripcion, empresa_derivadora))
            conn.commit()
            return redirect(url_for('index'))
        except sqlite3.Error as e:
            print(f"Error al agregar equipo: {e}")
            return "Error al agregar equipo", 500
        finally:
            conn.close()

    return render_template('nuevo_equipo.html')

@app.route('/agregar_novedad/<int:id>', methods=['GET', 'POST'])
def agregar_novedad(id):
    if request.method == 'POST':
        try:
            novedad = request.form['novedad']
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('UPDATE equipos SET novedades = ? WHERE id = ?', (novedad, id))
            conn.commit()
            return redirect(url_for('index'))
        except sqlite3.Error as e:
            print(f"Error al agregar novedad: {e}")
            return "Error al agregar novedad", 500
        finally:
            conn.close()
    return render_template('agregar_novedad.html', id=id)

# Ruta para editar equipo
@app.route('/editar_equipo/<int:id>', methods=['GET', 'POST'])
def editar_equipo(id):
    create_table()
    conn = None  # Asegura que conn esté definido en el ámbito de la función
    try:
        if request.method == 'POST':
            nombre_cliente = request.form['nombre_cliente']
            telefono_cliente = request.form['telefono_cliente']
            email_cliente = request.form['email_cliente']
            marca = request.form['marca']
            modelo = request.form['modelo']
            tipo = request.form['tipo']
            numero_serie = request.form['numero_serie']
            descripcion = request.form['descripcion']

            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE equipos
                SET nombre_cliente = ?, telefono_cliente = ?, email_cliente = ?, marca = ?, modelo = ?, tipo = ?, numero_serie = ?, descripcion = ?
                WHERE id = ?
            ''', (nombre_cliente, telefono_cliente, email_cliente, marca, modelo, tipo, numero_serie, descripcion, id))
            conn.commit()
            return redirect(url_for('index'))

        else:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM equipos WHERE id = ?', (id,))
            equipo = cursor.fetchone()
            if equipo is None:
                return "Equipo no encontrado", 404
            return render_template('editar_equipo.html', equipo=equipo)

    except sqlite3.Error as e:
        print(f"Error al editar el equipo: {e}")
        return "Error al editar el equipo", 500

    finally:
        if conn:
            conn.close()
        conn.close()

# Función para obtener equipo por id
def obtener_equipo_por_id(id):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM equipos WHERE id = ?', (id,))
        equipo = cursor.fetchone()
        if equipo:
            return {
                'id': equipo[0],
                'nombre_cliente': equipo[1],
                'telefono_cliente': equipo[2],
                'email_cliente': equipo[3],
                'marca': equipo[4],
                'modelo': equipo[5],
                'tipo': equipo[6],
                'numero_serie': equipo[7],
                'descripcion': equipo[8],
                'estado': equipo[9],
                'empresa_derivadora': equipo[10],
                'novedades': equipo[11]
            }
        return None
    except sqlite3.Error as e:
        print(f"Error al obtener equipo por id: {e}")
        return None
    finally:
        conn.close()

@app.route('/eliminar_equipo/<int:id>', methods=['POST'])
def eliminar_equipo(id):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM equipos WHERE id = ?', (id,))
        conn.commit()
        return redirect(url_for('index'))
    except sqlite3.Error as e:
        print(f"Error al eliminar equipo: {e}")
        return "Error al eliminar equipo", 500
    finally:
        conn.close()

@app.route('/actualizar_estado/<int:id>', methods=['POST'])
def actualizar_estado(id):
    nuevo_estado = request.form['estado']
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('UPDATE equipos SET estado = ? WHERE id = ?', (nuevo_estado, id))
        conn.commit()
        return redirect(url_for('consulta', id=id))
    except sqlite3.Error as e:
        print(f"Error al actualizar estado: {e}")
        return "Error al actualizar estado", 500
    finally:
        conn.close()


# Ruta para emitir un remito en PDF
@app.route('/emitir_remito/<int:id>')
def emitir_remito(id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM equipos WHERE id = ?', (id,))
    equipo = cursor.fetchone()
    conn.close()

    if not equipo:
        return "No se encontró el equipo con el ID proporcionado.", 404

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Orden de Trabajo", ln=True, align='C')
    
    pdf.set_font("Arial", size=12)
    pdf.ln(10)  # Espacio antes de la tabla

    # Crear la cabecera de la tabla
    pdf.set_font("Arial", "B", 12)
    headers = ["Campo", "Detalle"]
    column_width = pdf.w / 2.5  # Dividir el ancho en dos columnas

    for header in headers:
        pdf.cell(column_width, 10, header, border=1, align='C')
    pdf.ln()

    # Rellenar la tabla con los detalles del equipo
    pdf.set_font("Arial", size=12)
    data = [
        ("ID del Equipo", str(equipo[0])),
        ("Nombre del Cliente", equipo[1]),
        ("Teléfono", equipo[2]),
        ("Email", equipo[3]),
        ("Marca", equipo[4]),
        ("Modelo", equipo[5]),
        ("Tipo", equipo[6]),
        ("Número de Serie", equipo[7]),
        ("Descripción", equipo[8]),
        ("Estado", equipo[9]),
        ("Empresa Derivadora", equipo[10]),
        ("Novedades", equipo[11] if equipo[11] else "N/A")
    ]

    for row in data:
        for item in row:
            pdf.cell(column_width, 10, str(item), border=1)
        pdf.ln()

    # Verificar si la carpeta static existe y si no, crearla
    if not os.path.exists('static'):
        os.makedirs('static')

    # Guardar el archivo PDF
    pdf_path = f'static/remito_{id}.pdf'
    pdf.output(pdf_path)

    return f"El remito ha sido generado y guardado en {pdf_path}."




@app.route('/consulta/<int:id>')
def consulta(id):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM equipos WHERE id = ?', (id,))
        equipo = cursor.fetchone()

        if equipo is None:
            return "Equipo no encontrado", 404

        return render_template('consulta.html', equipo=equipo)

    except sqlite3.Error as e:
        print(f"Error al consultar el equipo: {e}")
        return "Error al consultar el equipo", 500

    finally:
        if conn:
            conn.close()

@app.route('/editar_estado/<int:id>', methods=['GET', 'POST'])
def editar_estado(id):
    if request.method == 'POST':
        nuevo_estado = request.form['estado']
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('UPDATE equipos SET estado = ? WHERE id = ?', (nuevo_estado, id))
            conn.commit()
            return redirect(url_for('index'))
        except sqlite3.Error as e:
            print(f"Error al actualizar el estado: {e}")
            return "Error al actualizar el estado", 500
        finally:
            conn.close()
    else:
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM equipos WHERE id = ?', (id,))
            equipo = cursor.fetchone()
            if equipo:
                return render_template('editar_estado.html', equipo=equipo)
            else:
                return "Equipo no encontrado", 404
        finally:
            conn.close()



# Ejecutar la aplicación
if __name__ == '__main__':
    app.run(debug=True)
