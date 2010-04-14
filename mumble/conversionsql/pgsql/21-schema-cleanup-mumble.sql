-- Model: Mumble
BEGIN;
ALTER TABLE "mumble_mumble"
        DROP COLUMN "dbus";
ALTER TABLE "mumble_mumble"
        DROP COLUMN "url";
ALTER TABLE "mumble_mumble"
        DROP COLUMN "motd";
ALTER TABLE "mumble_mumble"
        DROP COLUMN "passwd";
ALTER TABLE "mumble_mumble"
        DROP COLUMN "supw";
ALTER TABLE "mumble_mumble"
        DROP COLUMN "users";
ALTER TABLE "mumble_mumble"
        DROP COLUMN "bwidth";
ALTER TABLE "mumble_mumble"
        DROP COLUMN "sslcrt";
ALTER TABLE "mumble_mumble"
        DROP COLUMN "sslkey";
ALTER TABLE "mumble_mumble"
        DROP COLUMN "obfsc";
ALTER TABLE "mumble_mumble"
        DROP COLUMN "player";
ALTER TABLE "mumble_mumble"
        DROP COLUMN "channel";
ALTER TABLE "mumble_mumble"
        DROP COLUMN "defchan";
ALTER TABLE "mumble_mumble"
        DROP COLUMN "booted";

ALTER TABLE "mumble_mumble"
        ALTER COLUMN "server_id" SET NOT NULL;
COMMIT;