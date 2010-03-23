INSERT INTO "mumble_mumble_new"
SELECT
  "mumble_mumble"."id",
  "mumble_mumbleserver"."id",
  "mumble_mumble"."name",
  "mumble_mumble"."srvid",
  "mumble_mumble"."addr",
  "mumble_mumble"."port",
  ''
FROM "mumble_mumble" INNER JOIN "mumble_mumbleserver"
WHERE "mumble_mumbleserver"."dbus" = "mumble_mumble"."dbus";
