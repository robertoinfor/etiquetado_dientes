import tkinter as tk
from tkinter import filedialog
import cv2
from PIL import Image, ImageTk
import os

class Etiquetador:
    def __init__(self, root):
        self.root = root
        self.root.title("Etiquetador IA")
        root.geometry("800x600")

        # Frame de leyenda
        self.frame_leyenda = tk.Frame(root, bg="lightgray", padx=10, pady=5)
        self.frame_leyenda.pack(side="top", fill="x")

        leyenda_text = (
            "U: Deshacer último rect. | Q: Clase 0 (Roja) | W: Clase 1 (Azul) | E: Clase 2 (Verde) | R: Clase 3 (Amarilla) | "
            "C: Cambiar clase rect. seleccionado | Delete: Eliminar rect. | "
            "A: Anterior | D: Siguiente | Click Der: Seleccionar rect."
        )
        tk.Label(self.frame_leyenda, text=leyenda_text, bg="lightgray", font=("Arial", 9), wraplength=800, justify="left").pack()

        self.frame_botones = tk.Frame(root)
        self.frame_botones.pack(side="top", fill="x", pady=10)

        self.btn_cargar = tk.Button(self.frame_botones, text="Cargar Imágenes", command=self.cargar_imagenes)
        self.btn_cargar.pack(side="left", padx=5, pady=5)

        self.btn_guardar = tk.Button(self.frame_botones, text="Guardar YOLO", command=self.guardar_actual)
        self.btn_guardar.pack(side="left", padx=5, pady=5)

        self.canvas = tk.Canvas(root, cursor="cross")
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<ButtonPress-1>", self.iniciar_rect)
        self.canvas.bind("<B1-Motion>", self.dibujar_rect)
        self.canvas.bind("<ButtonRelease-1>", self.finalizar_rect)
        self.canvas.bind("<Button-3>", self.seleccionar_rect)  # Click derecho

        self.root.bind("a", self.tecla_anterior)
        self.root.bind("d", self.tecla_siguiente)
        self.clase_actual = 0
        self.root.bind("q", lambda e: self.cambiar_clase(0))
        self.root.bind("w", lambda e: self.cambiar_clase(1))
        self.root.bind("e", lambda e: self.cambiar_clase(2))
        self.root.bind("r", lambda e: self.cambiar_clase(3))
        self.root.bind("k", self.eliminar_seleccionado)
        self.root.bind("Delete", self.eliminar_seleccionado)
        self.root.bind("c", self.cambiar_clase_seleccionado)
        self.root.bind("u", self.deshacer)
        self.imagenes = []
        self.rutas = []
        self.tk_imagenes = []
        self.boxes_por_imagen = []
        self.indice = 0
        self.rect = None
        self.start_x = None
        self.start_y = None
        self.rect_seleccionado = None
        self.editando = False
        self.resize_mode = None  # "move", "resize_nw", "resize_ne", "resize_sw", "resize_se"

    def seleccionar_rect(self, event):
        if not self.imagenes:
            return
        
        # Buscar si hay un rectángulo en esta posición
        encontrado = False
        for i, box in enumerate(self.boxes_por_imagen[self.indice]):
            x1, y1, x2, y2, clase = box
            # Verificar si el click está dentro del rectángulo
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.rect_seleccionado = i
                self.editando = True
                self.start_x = event.x
                self.start_y = event.y
                
                # Detectar modo de redimensionamiento (esquinas)
                if abs(event.x - x1) < 10 and abs(event.y - y1) < 10:
                    self.resize_mode = "resize_nw"
                elif abs(event.x - x2) < 10 and abs(event.y - y1) < 10:
                    self.resize_mode = "resize_ne"
                elif abs(event.x - x1) < 10 and abs(event.y - y2) < 10:
                    self.resize_mode = "resize_sw"
                elif abs(event.x - x2) < 10 and abs(event.y - y2) < 10:
                    self.resize_mode = "resize_se"
                else:
                    self.resize_mode = "move"
                
                encontrado = True
                self.mostrar_imagen()
                return
        
        if not encontrado:
            self.rect_seleccionado = None
            self.editando = False
            self.mostrar_imagen()

    def iniciar_rect(self, event):
        if not self.imagenes or self.editando:
            return
        self.start_x = min(max(event.x, 0), self.tk_imagenes[self.indice].width())
        self.start_y = min(max(event.y, 0), self.tk_imagenes[self.indice].height())
        colores = ["red", "blue", "green", "yellow"]
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y,
            self.start_x, self.start_y,
            outline=colores[self.clase_actual], width=2
        )

    def dibujar_rect(self, event):
        if self.editando and self.rect_seleccionado is not None:
            # Modo edición de rectángulo existente
            box = self.boxes_por_imagen[self.indice][self.rect_seleccionado]
            x1, y1, x2, y2, clase = box
            
            dx = event.x - self.start_x
            dy = event.y - self.start_y
            
            if self.resize_mode == "move":
                x1 = min(max(x1 + dx, 0), self.tk_imagenes[self.indice].width())
                y1 = min(max(y1 + dy, 0), self.tk_imagenes[self.indice].height())
                x2 = min(max(x2 + dx, 0), self.tk_imagenes[self.indice].width())
                y2 = min(max(y2 + dy, 0), self.tk_imagenes[self.indice].height())
            elif self.resize_mode == "resize_nw":
                x1 = min(max(event.x, 0), x2 - 10)
                y1 = min(max(event.y, 0), y2 - 10)
            elif self.resize_mode == "resize_ne":
                x2 = min(max(event.x, x1 + 10), self.tk_imagenes[self.indice].width())
                y1 = min(max(event.y, 0), y2 - 10)
            elif self.resize_mode == "resize_sw":
                x1 = min(max(event.x, 0), x2 - 10)
                y2 = min(max(event.y, y1 + 10), self.tk_imagenes[self.indice].height())
            elif self.resize_mode == "resize_se":
                x2 = min(max(event.x, x1 + 10), self.tk_imagenes[self.indice].width())
                y2 = min(max(event.y, y1 + 10), self.tk_imagenes[self.indice].height())
            
            self.boxes_por_imagen[self.indice][self.rect_seleccionado] = (x1, y1, x2, y2, clase)
            self.start_x = event.x
            self.start_y = event.y
            self.mostrar_imagen()
            
        elif self.rect:
            x = min(max(event.x, 0), self.tk_imagenes[self.indice].width())
            y = min(max(event.y, 0), self.tk_imagenes[self.indice].height())
            self.canvas.coords(self.rect, self.start_x, self.start_y, x, y)
            if hasattr(self, "temp_text") and self.temp_text:
                self.canvas.delete(self.temp_text)
            self.temp_text = self.canvas.create_text(self.start_x + 5, self.start_y + 5,
                                                 text=str(self.clase_actual),
                                                 anchor="nw",
                                                 fill=["red","blue","green","yellow"][self.clase_actual],
                                                 font=("Arial", 12, "bold"))
            self.canvas.itemconfig(self.rect, outline=["red","blue","green","yellow"][self.clase_actual])

    def finalizar_rect(self, event):
        if self.editando:
            self.editando = False
            # NO pongas: self.rect_seleccionado = None
            # Así el rectángulo sigue seleccionado para más ediciones
            self.resize_mode = None
            self.mostrar_imagen()
            return
            
        if self.rect:
            x = min(max(event.x, 0), self.tk_imagenes[self.indice].width())
            y = min(max(event.y, 0), self.tk_imagenes[self.indice].height())

            x1 = min(self.start_x, x)
            y1 = min(self.start_y, y)
            x2 = max(self.start_x, x)
            y2 = max(self.start_y, y)

            self.boxes_por_imagen[self.indice].append((x1, y1, x2, y2, self.clase_actual))
            print(f"Imagen {self.indice+1} - Bounding box:", x1, y1, x2, y2)

            self.rect = None
            self.temp_text = None
            self.mostrar_imagen()

    def eliminar_seleccionado(self, event=None):
        if self.rect_seleccionado is not None:
            self.boxes_por_imagen[self.indice].pop(self.rect_seleccionado)
            self.rect_seleccionado = None
            self.editando = False
            self.resize_mode = None
            print(f"Rectángulo eliminado")
            self.mostrar_imagen()
        else:
            print("Selecciona un rectángulo primero (click derecho)")

    def cambiar_clase_seleccionado(self, event=None):
        if self.rect_seleccionado is not None:
            box = self.boxes_por_imagen[self.indice][self.rect_seleccionado]
            x1, y1, x2, y2, clase = box
            nueva_clase = (clase + 1) % 4
            self.boxes_por_imagen[self.indice][self.rect_seleccionado] = (x1, y1, x2, y2, nueva_clase)
            print(f"Clase del rectángulo cambiada a: {nueva_clase}")
            self.mostrar_imagen()
        else:
            print("Selecciona un rectángulo primero (click derecho)")

    def deshacer(self, event=None):
        if self.boxes_por_imagen[self.indice]:
            self.boxes_por_imagen[self.indice].pop()
            self.mostrar_imagen()
            print("Último rectángulo deshecho")
        else:
            print("No hay rectángulos para deshacer")

    def cambiar_clase(self, clase):
        self.clase_actual = clase
        
        # Si hay un rectángulo seleccionado, también cambiar su clase
        if self.rect_seleccionado is not None:
            box = self.boxes_por_imagen[self.indice][self.rect_seleccionado]
            x1, y1, x2, y2, _ = box
            self.boxes_por_imagen[self.indice][self.rect_seleccionado] = (x1, y1, x2, y2, clase)
            self.mostrar_imagen()
        
        print(f"Clase actual: {self.clase_actual}")

    def cargar_imagenes(self):
        rutas = filedialog.askopenfilenames(title="Selecciona hasta 5 imágenes")
        if not rutas:
            return
        rutas = rutas[:5]

        self.imagenes.clear()
        self.tk_imagenes.clear()
        self.boxes_por_imagen.clear()
        self.rutas = rutas
        self.indice = 0

        for ruta in rutas:
            img = cv2.imread(ruta)
            if img is None:
                print(f"Error: No se pudo cargar la imagen {ruta}")
                continue
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Redimensionar para que quepa en la ventana sin zoom excesivo
            h, w = img.shape[:2]
            max_w, max_h = 750, 450  # Máximo disponible en el canvas
            escala = min(max_w/w, max_h/h, 1.0)
            if escala < 1.0:
                nuevo_w = int(w * escala)
                nuevo_h = int(h * escala)
                img = cv2.resize(img, (nuevo_w, nuevo_h))
            
            self.imagenes.append(img)
            self.tk_imagenes.append(ImageTk.PhotoImage(Image.fromarray(img)))
            self.boxes_por_imagen.append([])

        self.mostrar_imagen()

    def mostrar_imagen(self):
        self.canvas.delete("all")
        if not self.imagenes:
            return
        self.canvas.config(width=self.tk_imagenes[self.indice].width(),
                           height=self.tk_imagenes[self.indice].height())
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_imagenes[self.indice])

        colores = ["red", "blue", "green", "yellow"]

        for i, box in enumerate(self.boxes_por_imagen[self.indice]):
            x1, y1, x2, y2, clase = box
            # Resaltar si está seleccionado
            width = 4 if i == self.rect_seleccionado else 2
            self.canvas.create_rectangle(x1, y1, x2, y2,
                                        outline=colores[clase],
                                        width=width)
            self.canvas.create_text(x1 + 5, y1 + 5,
                                   text=str(clase),
                                   anchor="nw",
                                   fill=colores[clase],
                                   font=("Arial", 12, "bold"))

        nombre_imagen = os.path.basename(self.rutas[self.indice]) if self.rutas else "Sin imagen"
        self.root.title(f"Etiquetador IA - {nombre_imagen} ({self.indice+1}/{len(self.imagenes)})")

    def guardar_actual(self):
        if not self.imagenes:
            return
        ruta_img = self.rutas[self.indice]
        ruta_txt = os.path.splitext(ruta_img)[0] + ".txt"
        self.guardar_yolo(ruta_txt, self.imagenes[self.indice], self.boxes_por_imagen[self.indice])
        self.guardar_imagen_editada()
        print(f"Guardado: {ruta_txt}")

    def guardar_yolo(self, ruta_txt, img, boxes):
        h, w, _ = img.shape
        with open(ruta_txt, "w") as f:
            for box in boxes:
                x1, y1, x2, y2, clase = box
                x_center = ((x1 + x2) / 2) / w
                y_center = ((y1 + y2) / 2) / h
                width = (x2 - x1) / w
                height = (y2 - y1) / h
                f.write(f"{clase} {x_center} {y_center} {width} {height}\n")

    def guardar_imagen_editada(self):
        if not self.imagenes:
            return
        ruta_img = self.rutas[self.indice]
        ruta_salida = os.path.splitext(ruta_img)[0] + "_editada.jpg"
        
        img = self.imagenes[self.indice].copy()
        colores_bgr = [(0, 0, 255), (255, 0, 0), (0, 255, 0), (0, 255, 255)]  # BGR para OpenCV
        
        for box in self.boxes_por_imagen[self.indice]:
            x1, y1, x2, y2, clase = box
            color = colores_bgr[clase]
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            cv2.putText(img, str(clase), (x1 + 5, y1 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        cv2.imwrite(ruta_salida, img_bgr)
        print(f"Imagen editada guardada: {ruta_salida}")

    def tecla_siguiente(self, event=None):
        if self.indice < len(self.imagenes) - 1:
            self.guardar_actual()
            self.indice += 1
            self.mostrar_imagen()

    def tecla_anterior(self, event=None):
        if self.indice > 0:
            self.guardar_actual()
            self.indice -= 1
            self.mostrar_imagen()


root = tk.Tk()
app = Etiquetador(root)
root.mainloop()