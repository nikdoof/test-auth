CREATE TABLE "mumble_mumbleuser_new" (
    "id" integer NOT NULL PRIMARY KEY,
    "mumbleid" integer NOT NULL,
    "name" varchar(200) NOT NULL,
    "password" varchar(200) NOT NULL,
    "server_id" integer NOT NULL REFERENCES "mumble_mumble" ("id"),
    "owner_id" integer REFERENCES "auth_user" ("id"),
    UNIQUE ("server_id", "owner_id"),
    UNIQUE ("server_id", "mumbleid")
);
