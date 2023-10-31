from pathlib import Path
import align


# Alineamiento de un archivo

result = align.align_images("img/image_00001.jpg", "img/plantilla.jpg")

print(result)
