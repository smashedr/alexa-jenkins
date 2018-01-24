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
        elif intent == 'GetSlaves':
            return get_total_nodes(event)
        elif intent == 'GetOnOffStatus':
            return get_on_off_status(event)
        elif intent == 'GetSlaveInfo':
            return get_slave_info(event)
        else:
            raise ValueError('Unknown Intent')
    except Exception as error:
        logger.exception(error)
        return alexa_resp('Error, {}.'.format(error), 'Error')


def get_slave_info(event):
    logger.info('GetSlaveInfo')
    try:
        # jenkins = init_jenkins(event)
        # nodes = jenkins.get_nodes()
        logger.info(event['request']['intent']['slots']['node']['value'])
        words = event['request']['intent']['slots']['node']['value']
        search_terms = words.split(' ')
        try:
            logger.info(event['request']['intent']['slots']['number']['value'])
            number = event['request']['intent']['slots']['number']['value']
            search_terms.append(number)
        except:
            pass

        jenkins = init_jenkins(event)
        nodes = jenkins.get_nodes()
        keys = nodes.keys()
        results = keys
        for term in search_terms:
            for k in keys:
                if term not in k.lower():
                    try:
                        results.remove(k)
                    except:
                        pass
        logger.info('results: {}'.format(results))
        speech = 'This will end well.'
        return alexa_resp(speech, 'Jenkins Slaves')
    except Exception as error:
        logger.exception(error)
        return alexa_resp('Error, {}.'.format(error), 'Error')


def get_on_off_status(event):
    logger.info('GetOnOffStatus')
    try:
        jenkins = init_jenkins(event)
        nodes = jenkins.get_nodes()
        online = 0
        for key in nodes.keys():
            n = jenkins.get_node(key)
            online += 1 if n.is_online() else 0
        total = len(nodes.keys())
        offline = total - online
        speech = ('Out of {} slaves, '
                  '{} are online and '
                  '{} are offline.').format(total, online, offline)
        return alexa_resp(speech, 'Slaves Online')
    except Exception as error:
        logger.exception(error)
        return alexa_resp('Error, {}.'.format(error), 'Error')


def get_total_nodes(event):
    logger.info('GetSlaves')
    try:
        jenkins = init_jenkins(event)
        nodes = jenkins.get_nodes()
        total = len(nodes.keys())
        speech = 'There are a total of {} slaves.'.format(total)
        return alexa_resp(speech, 'Jenkins Slaves')
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
