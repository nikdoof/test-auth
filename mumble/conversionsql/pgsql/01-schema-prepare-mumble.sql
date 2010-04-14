-- Model: Mumble
BEGIN;
ALTER TABLE "mumble_mumble"
        ADD "server_id" integer NULL REFERENCES "mumble_mumbleserver" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "mumble_mumble"
        ADD "display" varchar(200);
ALTER TABLE "mumble_mumble"
	ALTER "port" DROP NOT NULL;

CREATE INDEX "mumble_mumble_server_id" ON "mumble_mumble" ("server_id");

ALTER TABLE "mumble_mumble" DROP CONSTRAINT "mumble_mumble_addr_key";
COMMIT;
