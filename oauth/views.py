import logging
import random
import string
import urllib.parse
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from api.models import TokenDatabase
from jenkinsapi.jenkins import Jenkins

logger = logging.getLogger('app')
config = settings.CONFIG['app']


def has_success(request):
    """
    View  /success
    This is for debugging only
    You will be redirected back to Alexa
    I am not even sure if this is even used...
    """
    return render(request, 'oauth/success.html')


def has_error(request):
    """
    View  /error
    This is for debugging only
    Error handling does not yet exist
    """
    return render(request, 'oauth/error.html')


def privacy_policy(request):
    """
    View  /privacy
    This is copied from old project
    It will be removed and added to home
    """
    return render(request, 'oauth/privacy.html')


@require_http_methods(['GET'])
def do_authorize(request):
    """
    View  /oauth/authorize
    """
    log_req(request)
    try:
        if 'client_id' in request.GET:
            request.session['client_id'] = request.GET.get('client_id')
        if 'redirect_uri' in request.GET:
            request.session['redirect_uri'] = request.GET.get('redirect_uri')
        if 'response_type' in request.GET:
            request.session['response_type'] = request.GET.get('response_type')
        if 'state' in request.GET:
            request.session['state'] = request.GET.get('state')

        if request.session['client_id'] != config['client_id']:
            raise ValueError('Inivalid client_id')
        if request.session['redirect_uri'] not in \
                config['redirect_uris'].split(' '):
            raise ValueError('Inivalid redirect_uri')
        if request.session['response_type'] != 'code':
            raise ValueError('Inivalid response_type')
        if not request.session['state']:
            raise ValueError('Inivalid state')

        return render(request, 'oauth/authorize.html')
    except Exception as error:
        logger.exception(error)
        messages.add_message(
            request, messages.WARNING,
            'Invalid Request.',
            extra_tags='danger',
        )
        return redirect('error')


@require_http_methods(['POST'])
def do_verify(request):
    """
    View  /oauth/verify
    """
    log_req(request)
    try:
        _username = request.POST.get('username')
        _password = request.POST.get('password')
        _url = request.POST.get('url')

        try:
            jenkins = Jenkins(_url, username=_username, password=_password)
            logger.info(jenkins.version)
            if not jenkins.version:
                raise ValueError('Unknown Jenkins Version')
        except Exception as error:
            logger.exception(error)
            messages.add_message(
                request, messages.WARNING,
                'Error Authorizing Jenkins Server',
                extra_tags='danger',
            )
            return redirect('authorize')

        uuid = gen_rand(50)
        code = gen_rand(25)
        logger.info('uuid: {}'.format(uuid))
        logger.info('code: {}'.format(code))
        td = TokenDatabase(
            uuid=uuid,
            code=code,
            username=_username,
            password=_password,
            url=_url,
        )
        td.save()

        messages.add_message(
            request, messages.SUCCESS,
            'Successfully Authenticated Jenkins.',
            extra_tags='success',
        )
        get_vars = {
            'code': code, 'state': request.session['state']
        }
        url = request.session['redirect_uri']
        return redirect(url + '?' + urllib.parse.urlencode(get_vars))

    except Exception as error:
        logger.exception(error)
        messages.add_message(
            request, messages.SUCCESS,
            'Error: {}'.format(error),
            extra_tags='danger',
        )
        return redirect('authorize')


@csrf_exempt
@require_http_methods(['POST'])
def give_token(request):
    """
    View  /oauth/token
    """
    log_req(request)
    try:
        _code = request.POST.get('code')
        _client_id = request.POST.get('client_id')
        _client_secret = request.POST.get('client_secret')

        if _client_id != config['client_id']:
            logger.info('invalid_client_id')
            return JsonResponse(
                error_resp('invalid_client', 'ClientId is Invalid'), status=400
            )

        try:
            if _code:
                td = TokenDatabase.objects.get(code=_code)
                uuid = td.uuid
            else:
                raise ValueError('code null')
        except Exception as error:
            logger.exception(error)
            return JsonResponse(
                error_resp('invalid_code', 'Code is Invalid'), status=400
            )

        token_resp = {
            'access_token': uuid,
            'token_type': 'bearer',
        }
        return JsonResponse(token_resp)
    except Exception as error:
        logger.exception(error)
        return JsonResponse(
            error_resp('unknown_error', 'Unknown Error'), status=400
        )


def error_resp(error_code, error_msg):
    resp = {'ErrorCode': error_code, 'Error': error_msg}
    return resp


def gen_rand(length):
    return ''.join(
        random.choice(
            string.ascii_uppercase + string.digits
        ) for _ in range(length)
    )


def log_req(request):
    """
    DEBUGGING ONLY
    """
    data = ''
    if request.method == 'GET':
        logger.debug('GET')
        for key, value in request.GET.items():
            data += '"%s": "%s", ' % (key, value)
    if request.method == 'POST':
        logger.debug('POST')
        for key, value in request.POST.items():
            data += '"%s": "%s", ' % (key, value)
    data = data.strip(', ')
    logger.debug(data)
    json_string = '{%s}' % data
    return json_string
