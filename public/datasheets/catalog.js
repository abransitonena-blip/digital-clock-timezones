/*
 * Catálogo de hojas de datos (en español).
 * Para agregar una hoja desde el código: copia el PDF a la carpeta "pdf/"
 * (y, si quieres, una imagen de la primera página a "img/") y añade un objeto aquí.
 * También se pueden subir PDF desde la propia página (botón "Agregar hoja de datos");
 * esos quedan guardados en el navegador de quien los sube.
 */
window.CATALOGO = [
  {
    id: "ncep40t13gu",
    nombre: "MOSFET de potencia canal N Super Trench",
    parte: "NCEP40T13GU",
    fabricante: "Wuxi NCE Power",
    categoria: "MOSFET",
    proyecto: "",
    version: "V1.0",
    paginas: 8,
    descripcion:
      "MOSFET de 40 V y 130 A con RDS(ON) de 1.8 mΩ y baja carga de compuerta. Pensado para conmutación de alta frecuencia y rectificación síncrona (convertidores CC/CC). 100 % probado en UIS y ΔVds.",
    especificaciones: [
      ["VDS", "40 V"],
      ["ID", "130 A"],
      ["RDS(ON) @ 10 V", "1.8 mΩ típ."],
      ["RDS(ON) @ 4.5 V", "2.8 mΩ típ."],
      ["Qg", "49 nC típ."],
      ["Encapsulado", "DFN5X6-8L"],
      ["TJ máx.", "150 °C"]
    ],
    archivo: "pdf/NCEP40T13GU_Hoja_de_Datos_ES.pdf",
    imagen: "img/NCEP40T13GU.jpg",
    fuente: "http://www.ncepower.com"
  }
];
