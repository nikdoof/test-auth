INSERT INTO "mumble_mumbleuser_new"
SELECT
    "id",
    "mumbleid",
    "name",
    "password",
    "server_id",
    "owner_id"
FROM "mumble_mumbleuser";
