from pathlib import Path
import align

# Alineamiento de todos los telegramas (a partir del archivo de 15 GB de mega.io)
# Debe dejarse en la carpeta `generales_telegramas`:

provincias_nombres = {
    "01": "Capital Federal",
    "02": "Buenos Aires",
    "03": "Catamarca",
    "04": "Córdoba",
    "05": "Corrientes",
    "06": "Chaco",
    "07": "Chubut",
    "08": "Entre Ríos",
    "09": "Formosa",
    "10": "Jujuy",
    "11": "La Pampa",
    "12": "La Rioja",
    "13": "Mendoza",
    "14": "Misiones",
    "15": "Neuquén",
    "16": "Río Negro",
    "17": "Salta",
    "18": "San Juan",
    "19": "San Luis",
    "20": "Santa Cruz",
    "21": "Santa Fe",
    "22": "Santiago del Estero",
    "23": "Tucumán",
    "24": "Tierra del Fuego",
}

for provincia in provincias_nombres:
    image_paths = list(Path("generales_telegramas").glob(f"{provincia}*.jpg"))

    result = align.align_images(
        image_paths, f"templates/generales_telegrama_{provincia}.png"
    )

    print(result)
