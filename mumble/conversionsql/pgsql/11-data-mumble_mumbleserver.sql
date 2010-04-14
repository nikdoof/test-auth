BEGIN;
INSERT INTO "mumble_mumbleserver" ( "dbus", "secret" )
SELECT DISTINCT "dbus", ''
FROM "mumble_mumble";
COMMIT;
