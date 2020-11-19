CREATE TABLE "Organisations" (
	"id"	INTEGER,
	"name"	TEXT,
	"emailDomain"	TEXT,
	"userCount"	INTEGER,
	"points"	INTEGER,
	PRIMARY KEY("id")
);

CREATE TABLE "Users" (
	"id"	INTEGER,
	"name"	TEXT,
	"email"	TEXT,
	"orgId"	INTEGER,
	"points"	INTEGER,
	PRIMARY KEY("id")
);