# Event invitations

This app helps people organize events, such as a team lunch or a study session. Users can create an event, choose who to invite, change the details, or cancel it.

Each event has a title, a description, and a list of invited user IDs. The existing users are `u1`, `u2`, and `u3`. Invitations are just saved user IDs; the app does not send messages.

Complete the four methods in [src/service.c](src/service.c). The rest of the app is provided. Events are stored in memory, so no database is needed.

## service_create

- Save a new event and return it with a unique ID. Never reuse an ID, even after an event is deleted.
- If no description or invitees are given, use an empty description and an empty list.
- Keep the text and invitee order as given.
- Report an error if an invitee does not exist or appears more than once. Do not save the event in that case.

## service_read

- Return the event with the given ID.
- Report an error if it does not exist.

## service_update

- Replace the event's details and return the updated event. Keep its ID.
- If no description or invitees are given, clear those fields. An empty invitee list also clears invitations.
- Keep the text and invitee order as given.
- Report an error if the event does not exist. This should be the error even if the invitees are also invalid.
- Report an error if an invitee does not exist or appears more than once. Leave the event unchanged in that case.

## service_delete

- Remove the event with the given ID.
- Report an error if it does not exist or was already deleted.
- Once deleted, the event can no longer be read or updated.

Changes to one event must not change other events or users.

The starter's eight event service checks fail because these methods are unfinished. Use [commands.md](commands.md) to run the tests.
