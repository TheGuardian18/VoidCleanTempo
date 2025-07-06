# -*- coding: utf-8 -*-
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import psutil
import textwrap
from datetime import datetime
import pandas as pd
import threading
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

purpose_keywords = {
    ".log": "Archivo de registro del sistema o aplicaciones",
    ".tmp": "Archivo temporal generado por programas",
    ".temp": "Archivo temporal generado automáticamente",
    ".bak": "Copia de seguridad de un archivo antiguo",
    ".dmp": "Volcado de memoria para depurar errores",
    ".cache": "Archivo de caché usado para acelerar procesos",
    ".old": "Versión anterior de un archivo reemplazado",
    ".msi": "Instalador de software temporal",
    ".config": "Archivo de configuración o parámetros",
    ".json": "Datos temporales estructurados",
    ".txt": "Archivo de texto auxiliar o log de errores",
    ".zip": "Archivo comprimido generado temporalmente",
    ".csv": "Datos temporales en tabla (Excel)",
    ".etl": "Archivo de seguimiento de eventos del sistema",
    ".wer": "Informe de errores de Windows",
}

opciones_orden_map = {
    "Peso (mayor a menor)": "peso_mayor",
    "Peso (menor a mayor)": "peso_menor",
    "Fecha (más reciente)": "recientes",
    "Fecha (más antiguo)": "antiguos",
    "Nombre (A-Z)": "nombre_az",
    "Nombre (Z-A)": "nombre_za"
}

temp_path = os.environ.get("TEMP", "/tmp")
historial_eliminados = []
total_archivos = 0
checkbox_vars = {}
no_accesibles = 0
archivos_encontrados = []  # <--- NUEVA VARIABLE GLOBAL

def mostrar_ventana_proceso():
    ventana_proceso = tk.Toplevel(ventana)
    ventana_proceso.title("Cargando...")
    ventana_proceso.geometry("300x100")
    ventana_proceso.resizable(False, False)
    ventana_proceso.grab_set()
    ventana_proceso.attributes("-topmost", True)

    label = tk.Label(ventana_proceso, text="En proceso, espera por favor...", font=("Arial", 10, "bold"))
    label.pack(pady=(15, 5))

    barra = ttk.Progressbar(ventana_proceso, mode="indeterminate", length=250)
    barra.pack(pady=5)
    barra.start(10)

    return ventana_proceso

def actualizar_barra_almacenamiento():
    disco = os.path.splitdrive(temp_path)[0] or "C:"
    uso = psutil.disk_usage(disco)
    porcentaje = uso.percent
    barra_almacenamiento['value'] = porcentaje

    if porcentaje <= 50:
        barra_almacenamiento.configure(style="Verde.Horizontal.TProgressbar")
    elif porcentaje <= 80:
        barra_almacenamiento.configure(style="Naranja.Horizontal.TProgressbar")
    else:
        barra_almacenamiento.configure(style="Rojo.Horizontal.TProgressbar")

    label_almacenamiento.config(text=f"Uso de almacenamiento en {disco}: {porcentaje}%")

def actualizar_archivos():
    progress_bar.pack(fill="x", padx=20, pady=(5, 10))
    progress_var.set(0)
    btn_actualizar.config(state="disabled")

    # Mostrar ventana emergente de proceso
    ventana_cargando = mostrar_ventana_proceso()

    # Ejecutar carga en hilo separado
    threading.Thread(target=lambda: cargar_archivos_con_progreso_con_ventana(ventana_cargando)).start()

def cargar_archivos_con_progreso_con_ventana(ventana_cargando):
    cargar_archivos_con_progreso()
    ventana.after(100, ventana_cargando.destroy)

def get_file_description(nombre):
    ext = os.path.splitext(nombre)[1].lower()
    return purpose_keywords.get(ext, "Archivo temporal no clasificado del sistema")

def is_file_locked(filepath):
    try:
        os.rename(filepath, filepath)
        return False
    except:
        return True

def cargar_archivos_con_progreso():
    global total_archivos, no_accesibles, archivos_encontrados
    for widget in frame_archivos.winfo_children():
        widget.destroy()
    checkbox_vars.clear()
    archivos = []
    no_accesibles = 0

    try:
        lista = os.listdir(temp_path)
    except Exception as e:
        messagebox.showerror("Error", f"No se puede acceder al directorio TEMP:\n{e}")
        return

    total_items = len(lista)
    procesados = 0

    for archivo in lista:
        ruta = os.path.join(temp_path, archivo)
        try:
            if os.path.isfile(ruta):
                archivos.append({
                    "ruta": ruta,
                    "nombre": archivo,
                    "descripcion": get_file_description(archivo),
                    "estado": "En uso" if is_file_locked(ruta) else "Libre",
                    "ram": "-",
                    "peso": "-",
                    "fecha": datetime.fromtimestamp(os.path.getctime(ruta)).strftime("%d-%m-%Y %H:%M"),
                    "size": os.path.getsize(ruta),
                    "ctime": os.path.getctime(ruta)
                })
        except:
            no_accesibles += 1

        procesados += 1
        if total_items:
            progress = int(procesados / total_items * 100)
            ventana.after(1, progress_var.set, progress)

    total_archivos = len(archivos)
    label_total.config(text=f"Archivos temporales encontrados: {total_archivos}")

    orden = opciones_orden_map.get(combo_orden.get(), "original")
    if orden == "peso_mayor":
        archivos.sort(key=lambda x: x["size"], reverse=True)
    elif orden == "peso_menor":
        archivos.sort(key=lambda x: x["size"])
    elif orden == "recientes":
        archivos.sort(key=lambda x: x["ctime"], reverse=True)
    elif orden == "antiguos":
        archivos.sort(key=lambda x: x["ctime"])
    elif orden == "nombre_az":
        archivos.sort(key=lambda x: x["nombre"].lower())
    elif orden == "nombre_za":
        archivos.sort(key=lambda x: x["nombre"].lower(), reverse=True)

    archivos_encontrados = archivos.copy()  # <--- ACTUALIZA LA VARIABLE GLOBAL

    columnas = 2
    for idx, archivo in enumerate(archivos):
        row = idx // columnas
        col = idx % columnas

        frame = ttk.Frame(frame_archivos, borderwidth=2, relief="groove", padding=10)
        frame.grid(row=row, column=col, padx=10, pady=8, sticky="nsew")

        nombre_formateado = "\n".join(textwrap.wrap(archivo["nombre"], width=100))
        color_estado = "green" if archivo["estado"] == "Libre" else "red"

        ttk.Label(frame, text=f"Nombre: {nombre_formateado}", font=("Arial", 10, "bold")).pack(anchor="w")
        ttk.Label(frame, text=f"Descripción: {archivo['descripcion']}", wraplength=400).pack(anchor="w", pady=(2, 0))
        ttk.Label(frame, text=f"Estado: {archivo['estado']}", foreground=color_estado).pack(anchor="w")
        ttk.Label(frame, text=f"Fecha de creación: {archivo['fecha']}").pack(anchor="w")

        var = tk.BooleanVar()
        chk = ttk.Checkbutton(frame, text="Seleccionar para eliminar", variable=var)
        chk.pack(anchor="w", pady=(5, 0))
        checkbox_vars[archivo["ruta"]] = (var, archivo)

    if no_accesibles > 0:
        messagebox.showwarning("Advertencia", f"{no_accesibles} archivo(s) no pudieron accederse por permisos o bloqueo.")

    ventana.after(1, lambda: progress_bar.pack_forget())
    btn_actualizar.config(state="normal")

def cambio_orden(event=None):
    actualizar_archivos()

def marcar_todo():
    for var, _ in checkbox_vars.values():
        var.set(True)

def desmarcar_todo():
    for var, _ in checkbox_vars.values():
        var.set(False)

def eliminar_archivos():
    seleccionados = [(ruta, datos) for ruta, (var, datos) in checkbox_vars.items() if var.get()]
    total = len(seleccionados)

    if total == 0:
        messagebox.showinfo("Aviso", "No seleccionaste ningún archivo para eliminar.")
        return

    confirmar = messagebox.askyesno("Confirmar eliminación", f"¿Eliminar {total} archivo(s) seleccionados?")
    if not confirmar:
        return

    eliminados = 0
    errores = 0

    for ruta, datos in seleccionados:
        try:
            if not is_file_locked(ruta):
                os.remove(ruta)
                eliminados += 1
                historial_eliminados.append({
                    "Nombre": datos["nombre"],
                    "Descripción": datos["descripcion"],
                    "Peso": datos["peso"],
                    "RAM estimada": datos["ram"],
                    "Fecha de creación": datos["fecha"],
                    "Fecha Eliminación": datetime.now().strftime("%d-%m-%Y %H:%M")
                })
            else:
                errores += 1
        except:
            errores += 1

    messagebox.showinfo("Resultado", f"Eliminados: {eliminados}. Errores: {errores}.")
    actualizar_archivos()
    

def exportar_historial():
    if not historial_eliminados:
        messagebox.showinfo("Historial vacío", "Aún no has eliminado ningún archivo.")
        return

    archivo = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
    if archivo:
        df = pd.DataFrame(historial_eliminados)
        df.to_excel(archivo, index=False)

        wb = load_workbook(archivo)
        ws = wb.active
        for col in ws.columns:
            max_length = 0
            column = col[0].column
            for cell in col:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            adjusted_width = (max_length + 2)
            ws.column_dimensions[get_column_letter(column)].width = adjusted_width
        wb.save(archivo)

        messagebox.showinfo("Exportado", f"Historial exportado a:\n{archivo}")

def exportar_todos_a_excel():
    if not archivos_encontrados:
        messagebox.showinfo("Sin datos", "No hay archivos para exportar.")
        return

    archivo = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
    if archivo:
        datos = []
        for a in archivos_encontrados:
            datos.append({
                "Nombre": a["nombre"],
                "Descripción": a["descripcion"],
                "Estado": a["estado"],
                "Peso (bytes)": a["size"],
                "Fecha de creación": a["fecha"],
                "Ruta": a["ruta"]
            })
        df = pd.DataFrame(datos)
        df.to_excel(archivo, index=False)

        wb = load_workbook(archivo)
        ws = wb.active
        for col in ws.columns:
            max_length = 0
            column = col[0].column
            for cell in col:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            adjusted_width = (max_length + 2)
            ws.column_dimensions[get_column_letter(column)].width = adjusted_width
        wb.save(archivo)

        messagebox.showinfo("Exportado", f"Todos los archivos exportados a:\n{archivo}")

def mostrar_info_temp():
    messagebox.showinfo("¿Qué es %TEMP%?", "¿QUÉ ES LA CARPETA %TEMP%?\nLa carpeta %TEMP% es un directorio del sistema operativo donde se almacenan archivos temporales creados por aplicaciones, instaladores, procesos del sistema, y otras actividades. Estos archivos sirven como soporte durante la ejecución de programas o tareas.\n\nCon el tiempo, la carpeta %TEMP% puede llenarse de archivos innecesarios, lo que puede consumir espacio en disco y afectar el rendimiento del sistema.Eliminar archivos temporales de forma segura puede ayudar a:\n- Liberar espacio en disco.\n- Mejorar el rendimiento del sistema.\n- Eliminar restos de instalaciones incompletas o fallidas.NOTA: Algunos archivos pueden estar en uso y no podrán eliminarse hasta que la aplicación asociada se cierre o el sistema se reinicie.")

def mostrar_manual():
    messagebox.showinfo("Manual", "MANUAL DE USO DEL GESTOR TEMPORAL\n1. Presiona 'Actualizar archivos TEMP' para escanear la carpeta de archivos temporales.\n2. Puedes ordenar los resultados por peso, nombre o fecha usando el menú desplegable.\n3. Marca las casillas de los archivos que deseas eliminar.\n4. Presiona 'Eliminar seleccionados' para limpiarlos.\n5. Usa 'Exportar historial a Excel' si quieres guardar un registro de lo que se eliminó.\n6. Puedes seleccionar o deseleccionar todos los archivos con un solo clic usando los botones correspondientes.\n7. Observa el porcentaje de uso del almacenamiento en el disco que contiene la carpeta TEMP.\n8. Usa el botón '¿Qué es la carpeta %TEMP%?' para más información sobre su propósito.\n9. Cuando termines, presiona 'Salir del programa'.¡Mantén tu sistema más limpio y ordenado con este gestor!")

# INTERFAZ
def salir():
    ventana.quit()

# INTERFAZ
ventana = tk.Tk()
ventana.title("VoidCleanTempo")
ventana.geometry("1080x720")

style = ttk.Style()
style.theme_use("default")
style.configure("Verde.Horizontal.TProgressbar", foreground="green", background="green")
style.configure("Naranja.Horizontal.TProgressbar", foreground="orange", background="orange")
style.configure("Rojo.Horizontal.TProgressbar", foreground="red", background="red")

header = tk.Frame(ventana, bg="#d0e8ff", height=60)
header.pack(fill="x", padx=10, pady=(0, 0))

label_total = tk.Label(header, text="Archivos temporales encontrados: 0", bg="#d0e8ff", font=("Arial", 12, "bold"))
label_total.pack(side="left", padx=10, pady=5)

label_almacenamiento = tk.Label(header, text="Uso de almacenamiento: --%", bg="#d0e8ff", font=("Arial", 10))
label_almacenamiento.pack(side="top", padx=10, pady=(5, 0), anchor="w")

barra_almacenamiento = ttk.Progressbar(header, orient="horizontal", length=250, mode="determinate")
barra_almacenamiento.pack(side="top", padx=10, anchor="w")

estilo_botones = {"bg": "#b2d8f7", "fg": "black", "activebackground": "#91c8f6", "relief": "raised", "bd": 1, "font": ("Arial", 10, "bold")}

tk.Button(header, text="Exportar todos a Excel", command=exportar_todos_a_excel, **estilo_botones).pack(side="right", padx=5, pady=10)
tk.Button(header, text="Exportar historial a Excel", command=exportar_historial, **estilo_botones).pack(side="right", padx=5, pady=10)
tk.Button(header, text="Salir del programa", command=salir, **estilo_botones).pack(side="right", padx=5, pady=10)

main_frame = tk.Frame(ventana)
main_frame.pack(fill="both", expand=True)

frame_scroll = tk.Frame(main_frame)
frame_scroll.grid(row=0, column=0, sticky="nsew")

contenedor = tk.Canvas(frame_scroll)
scrollbar = ttk.Scrollbar(frame_scroll, orient="vertical", command=contenedor.yview)
frame_archivos = ttk.Frame(contenedor)

frame_archivos.bind("<Configure>", lambda e: contenedor.configure(scrollregion=contenedor.bbox("all")))
contenedor.create_window((0, 0), window=frame_archivos, anchor="nw")
contenedor.configure(yscrollcommand=scrollbar.set)
contenedor.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

main_frame.grid_rowconfigure(0, weight=1)
main_frame.grid_columnconfigure(0, weight=1)

panel_botones = tk.Frame(main_frame, bg="#f0f0f0", width=200)
panel_botones.grid(row=0, column=1, sticky="ns")

btn_eliminar = ttk.Button(panel_botones, text="Eliminar seleccionados", command=eliminar_archivos)
btn_eliminar.pack(pady=5, fill="x")

ttk.Button(panel_botones, text="Marcar todo", command=marcar_todo).pack(pady=5, fill="x")
ttk.Button(panel_botones, text="Desmarcar todo", command=desmarcar_todo).pack(pady=5, fill="x")

btn_actualizar = ttk.Button(panel_botones, text="Actualizar archivos TEMP", command=actualizar_archivos)
btn_actualizar.pack(pady=5, fill="x")

ttk.Button(panel_botones, text="¿Qué es la carpeta %TEMP%?", command=mostrar_info_temp).pack(pady=5, fill="x")

ttk.Button(panel_botones, text="Manual de la Aplicación", command=mostrar_manual).pack(pady=5, fill="x")

ttk.Label(panel_botones, text="Ordenar por:", background="#f0f0f0", font=("Arial", 10, "bold")).pack(pady=(10, 2), fill="x")

combo_orden = ttk.Combobox(panel_botones, values=list(opciones_orden_map.keys()), state="readonly")
combo_orden.set("Peso (mayor a menor)")
combo_orden.pack(pady=2, fill="x")
combo_orden.bind("<<ComboboxSelected>>", cambio_orden)

progress_var = tk.IntVar()
progress_bar = ttk.Progressbar(panel_botones, variable=progress_var, maximum=100, mode="determinate")

actualizar_barra_almacenamiento()
actualizar_archivos()
ventana.mainloop()