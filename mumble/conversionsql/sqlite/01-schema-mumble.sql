CREATE TABLE "mumble_mumble_new" (
    "id" integer NOT NULL PRIMARY KEY,
    "server_id" integer NOT NULL REFERENCES "mumble_mumbleserver" ("id"),
    "name" varchar(200) NOT NULL,
    "srvid" integer NOT NULL,
    "addr" varchar(200) NOT NULL,
    "port" integer,
    "display" varchar(200) NOT NULL,
    UNIQUE ("server_id", "srvid")
);
