-- Model: MumbleUser
BEGIN;
ALTER TABLE "mumble_mumbleuser"
        DROP COLUMN "isAdmin";
COMMIT;
