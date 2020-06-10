# Azure AD login demo with Starlette

First, copy `.env.sample` to `.env`:

    $ cp .env.sample .env

Create your Azure AD application and fill the client ID and secret
into `.env`, then run:

    $ python app.py

When registering your Azure AD application, remember to put:

    http://127.0.0.1:8000/callback

into the client redirect uris list.
