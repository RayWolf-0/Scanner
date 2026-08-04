CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE ROL_USUARIO (

    id_rol INTEGER PRIMARY KEY AUTOINCREMENT,

    nombre_rol TEXT NOT NULL

);
CREATE TABLE ESTADO_DOCUMENTO (

    id_estado INTEGER PRIMARY KEY AUTOINCREMENT,

    nombre_estado TEXT NOT NULL

);
CREATE TABLE PLANTILLA (

    id_plantilla INTEGER PRIMARY KEY AUTOINCREMENT,

    nombre TEXT NOT NULL,

    version INTEGER,

    ancho_pagina INTEGER,

    alto_pagina INTEGER

);
CREATE TABLE DOCUMENTO (

    id_documento INTEGER PRIMARY KEY AUTOINCREMENT,

    id_plantilla INTEGER NOT NULL,

    id_vendedor INTEGER NOT NULL,

    id_supervisor INTEGER,

    id_estado INTEGER NOT NULL,

    ruta_imagen TEXT,

    ruta_pdf_final TEXT,

    fecha_creacion DATETIME,

    FOREIGN KEY (id_plantilla) REFERENCES PLANTILLA(id_plantilla),

    FOREIGN KEY (id_vendedor) REFERENCES USUARIO(id_usuario),

    FOREIGN KEY (id_supervisor) REFERENCES USUARIO(id_usuario),

    FOREIGN KEY (id_estado) REFERENCES ESTADO_DOCUMENTO(id_estado)

);
CREATE TABLE AUDITORIA (

    id_auditoria INTEGER PRIMARY KEY AUTOINCREMENT,

    id_documento INTEGER NOT NULL,

    id_usuario INTEGER NOT NULL,

    observaciones TEXT,

    fecha_hora DATETIME,

    FOREIGN KEY (id_documento) REFERENCES DOCUMENTO(id_documento),

    FOREIGN KEY (id_usuario) REFERENCES USUARIO(id_usuario)

);
CREATE TABLE "USUARIO" (
	"id_usuario"	INTEGER,
	"id_rol"	INTEGER NOT NULL,
	"nombre"	TEXT NOT NULL,
	"apellido"	TEXT NOT NULL,
	"mail"	TEXT,
	"telefono"	TEXT,
	"run"	TEXT,
	"user"	TEXT NOT NULL,
	"contrasena"	INTEGER NOT NULL,
	PRIMARY KEY("id_usuario" AUTOINCREMENT),
	FOREIGN KEY("id_rol") REFERENCES "ROL_USUARIO"("id_rol")
);
CREATE TABLE "CAMPO_PLANTILLA" (
	"id_campo"	INTEGER,
	"id_plantilla"	INTEGER NOT NULL,
	"nombre_campo"	TEXT NOT NULL,
	"tipo_dato"	TEXT,
	"pos_x"	INTEGER,
	"ancho"	INTEGER,
	"alto"	INTEGER,
	"pos_y"	INTEGER,
	PRIMARY KEY("id_campo" AUTOINCREMENT),
	FOREIGN KEY("id_plantilla") REFERENCES "PLANTILLA"("id_plantilla")
);
CREATE TABLE "DATO_EXTRAIDO" (
	"id_dato"	INTEGER,
	"id_documento"	INTEGER NOT NULL,
	"id_campo"	INTEGER NOT NULL,
	"valor_extraido"	TEXT,
	"valor_corregido"	TEXT,
	PRIMARY KEY("id_dato" AUTOINCREMENT),
	FOREIGN KEY("id_campo") REFERENCES "CAMPO_PLANTILLA"("id_campo"),
	FOREIGN KEY("id_documento") REFERENCES "DOCUMENTO"("id_documento")
);
