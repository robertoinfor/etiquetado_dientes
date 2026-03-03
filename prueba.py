import tkinter as tk
from tkinter import filedialog
import cv2
from PIL import Image, ImageTk

class Etiquetador:
    def __init__(self, root):
        self.root = root
        self.root.title("Etiquetador IA")

        # Frame para los botones
        self.frame_botones = tk.Frame(root)
        self.frame_botones.pack(side="top", fill="x")

        self.btn_cargar = tk.Button(self.frame_botones, text="Cargar Imagen", command=self.cargar_imagen)
        self.btn_cargar.pack(side="left", padx=5, pady=5)

        self.btn_guardar = tk.Button(self.frame_botones, text="Guardar YOLO", command=self.guardar)
        self.btn_guardar.pack(side="left", padx=5, pady=5)

        # Canvas para la imagen
        self.canvas = tk.Canvas(root, cursor="cross")
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<ButtonPress-1>", self.iniciar_rect)
        self.canvas.bind("<B1-Motion>", self.dibujar_rect)
        self.canvas.bind("<ButtonRelease-1>", self.finalizar_rect)

        self.img = None
        self.tk_img = None
        self.rect = None
        self.start_x = None
        self.start_y = None
        self.boxes = []

    def cargar_imagen(self):
        ruta = filedialog.askopenfilename()
        if not ruta:
            return

        self.canvas.delete("all")
        self.boxes.clear()

        self.img = cv2.imread(ruta)
        self.img = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)

        self.mostrar_imagen()

    def mostrar_imagen(self):
        img_pil = Image.fromarray(self.img)
        self.tk_img = ImageTk.PhotoImage(img_pil)

        self.canvas.config(width=self.tk_img.width(), height=self.tk_img.height())
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)

    def iniciar_rect(self, event):
        if self.img is None:
            return

        self.start_x = event.x
        self.start_y = event.y

        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y,
            self.start_x, self.start_y,
            outline="red", width=2
        )

    def dibujar_rect(self, event):
        if self.rect:
            self.canvas.coords(self.rect,
                               self.start_x, self.start_y,
                               event.x, event.y)

    def finalizar_rect(self, event):
        if self.rect:
            x1 = min(self.start_x, event.x)
            y1 = min(self.start_y, event.y)
            x2 = max(self.start_x, event.x)
            y2 = max(self.start_y, event.y)

            self.boxes.append((x1, y1, x2, y2))
            print("Bounding box:", x1, y1, x2, y2)

            self.rect = None

    def guardar(self):
        if not self.img:
            return
        ruta_txt = filedialog.asksaveasfilename(defaultextension=".txt")
        if ruta_txt:
            self.guardar_yolo(ruta_txt)

    def guardar_yolo(self, ruta_txt):
        h, w, _ = self.img.shape
        with open(ruta_txt, "w") as f:
            for box in self.boxes:
                x1, y1, x2, y2 = box
                x_center = ((x1 + x2) / 2) / w
                y_center = ((y1 + y2) / 2) / h
                width = (x2 - x1) / w
                height = (y2 - y1) / h
                f.write(f"0 {x_center} {y_center} {width} {height}\n")

root = tk.Tk()
app = Etiquetador(root)
root.mainloop()