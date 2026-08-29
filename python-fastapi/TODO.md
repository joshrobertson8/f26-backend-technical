# Event invitations

This app helps people organize events, such as a team lunch or a study session. Users can create an event, choose who to invite, change the details, or cancel it.

Each event has a title, a description, and a list of invited user IDs. The existing users are `u1`, `u2`, and `u3`. Invitations are just saved user IDs; the app does not send messages.

Complete the four methods in [app/service.py](app/service.py). The rest of the app is provided. Events are stored in memory, so no database is needed.

## create

- Save a new event and return it with a unique ID. Never reuse an ID, even after an event is deleted.
- If no description or invitees are given, use an empty description and an empty list.
- Keep the text and invitee order as given.
- Report an error if an invitee does not exist or appears more than once. Do not save the event in that case.

## read

- Return the event with the given ID.
- Report an error if it does not exist.

## update

