import json
import logging
from django.shortcuts import HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from api.alexa import alexa_resp
from api.models import TokenDatabase
from jenkinsapi.jenkins import Jenkins

logger = logging.getLogger('app')


@require_http_methods(["GET"])
def api_home(request):
    log_req(request)
    return HttpResponse('API Online')


@csrf_exempt
@require_http_methods(["POST"])
def alexa_post(request):
    log_req(request)
    try:
        body = request.body.decode('utf-8')
        event = json.loads(body)
        logger.info(event)
        intent = event['request']['intent']['name']
        if intent == 'GetVersion':
            return get_version(event)
        elif intent == 'GetJobsTotal':
            return get_jobs_total(event)
        elif intent == 'BuildJob':
            return build_job(event)
        else:
            raise ValueError('Unknown Intent')
    except Exception as error:
        logger.exception(error)
        return alexa_resp('Error, {}.'.format(error), 'Error')


def get_version(event):
    logger.info('GetVersion')
    try:
        jenkins = init_jenkins(event)
        speech = 'Jenkins is running version {}.'.format(jenkins.version)
        return alexa_resp(speech, 'Jenkins Version')
    except Exception as error:
        logger.exception(error)
        return alexa_resp('Error, {}.'.format(error), 'Error')


def get_jobs_total(event):
    logger.info('GetJobsTotal')
    try:
        jenkins = init_jenkins(event)
        l = jenkins.get_jobs_list()
        speech = 'There are a total of {} jobs.'.format(len(l))
        return alexa_resp(speech, 'Total Jobs')
    except Exception as error:
        logger.exception(error)
        return alexa_resp('Error, {}.'.format(error), 'Error')


def build_job(event):
    logger.info('BuildJob')
    try:
        jenkins = init_jenkins(event)
        l = jenkins.get_jobs_list()
        resp = event['request']['intent']['slots']['job']['value']
        logger.info(resp)
        speech = 'Coming soon.'
        return alexa_resp(speech, 'Total Jobs')
    except Exception as error:
        logger.exception(error)
        return alexa_resp('Error, {}.'.format(error), 'Error')


def init_jenkins(event):
    logger.info('init_jenkins')
    p = TokenDatabase.objects.get(uuid=event['session']['user']['accessToken'])
    jenkins = Jenkins(
        p.url,
        username=p.username,
        password=p.password,
    )
    return jenkins


def log_req(request):
    """
    DEBUGGING ONLY
    """
    data = None
    if request.method == 'GET':
        data = 'GET: '
        for key, value in request.GET.items():
            data += '"%s": "%s", ' % (key, value)
    if request.method == 'POST':
        data = 'POST: '
        for key, value in request.POST.items():
            data += '"%s": "%s", ' % (key, value)
    if data:
        data = data.strip(', ')
        logger.info(data)
        json_string = '{%s}' % data
        return json_string
    else:
        return None
