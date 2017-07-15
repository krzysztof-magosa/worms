from Tkinter import Tk, Canvas, PhotoImage  # , mainloop

#

WIDTH, HEIGHT = 640, 480

#

window = Tk()
canvas = Canvas(window, width=WIDTH, height=HEIGHT, bg="#000000")
canvas.pack()
img = PhotoImage(width=WIDTH, height=HEIGHT)
canvas.create_image((WIDTH/2, HEIGHT/2), image=img, state="normal")

for x in range(WIDTH):
    for y in range(HEIGHT):
        color = "#ffffff"
        img.put(color, (x, y))

window.update_idletasks()
window.update()

while True:
    window.update_idletasks()
    window.update()
