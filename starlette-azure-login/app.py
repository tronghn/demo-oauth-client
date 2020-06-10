import json
import requests
from starlette.config import Config
from starlette.applications import Starlette
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import HTMLResponse, RedirectResponse
from authlib.integrations.starlette_client import OAuth

app = Starlette(debug=True)
app.add_middleware(SessionMiddleware, secret_key="super-secret-key")

config = Config('.env')
oauth = OAuth(config)

oauth.register(
    name='azure',
    server_metadata_url=config.get('WELL_KNOWN_URL'),
    client_kwargs={
        'scope': 'openid email profile https://graph.microsoft.com/.default',
        'response_mode': 'query',
        'response_type': 'code',
    },
)


@app.route('/')
async def homepage(request):
    user = request.session.get('user')
    if user:
        data = json.dumps(user, indent=4)
        userinfo = json.dumps(request.session.get('userinfo'), indent=4)
        html = (
            f'<pre><code>{data}</code></pre>'
            f'<pre><code>{userinfo}</code></pre>'
            '<a href="/logout"><button>logout</button></a>'
        )
        return HTMLResponse(html)
    return HTMLResponse('<a href="/login"><button>login</button></a>')


@app.route('/login')
async def login(request):
    redirect_uri = request.url_for('callback')
    return await oauth.azure.authorize_redirect(request, redirect_uri)


@app.route('/callback')
async def callback(request):
    token = await oauth.azure.authorize_access_token(request)
    user = await oauth.azure.parse_id_token(request, token)
    userinfo = user_info(token['access_token'])
    request.session['user'] = dict(user)
    request.session['userinfo'] = dict(userinfo)
    return RedirectResponse(url='/')


@app.route('/logout')
async def logout(request):
    post_logout_url = f"?post_logout_redirect_uri={request.url_for('homepage')}"
    logout_url = oauth.azure.server_metadata.get('end_session_endpoint', None)
    request.session.pop('user', None)
    if logout_url:
        return RedirectResponse(url=logout_url + post_logout_url)
    return RedirectResponse('/')


def user_info(token):
    headers = {'Authorization': f'Bearer {token}'}
    query = 'onPremisesSamAccountName,displayName,givenName,mail,officeLocation,surname,userPrincipalName,id,jobTitle'
    r = requests.get(f'https://graph.microsoft.com/v1.0/me?$select={query}', headers=headers)
    return r.json()


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=3000)
