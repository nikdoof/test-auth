UPDATE `mumble_mumble`
SET `server_id`=(
  SELECT `id`
  FROM `mumble_mumbleserver`
  WHERE `mumble_mumbleserver`.`dbus` = `mumble_mumble`.`dbus`
  );
