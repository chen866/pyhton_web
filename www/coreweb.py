import functools


def get(path):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.__method__ = 'GET'
        wrapper.__route__ = path
        return wrapper

    return decorator


def post(path):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.__method__ = 'POST'
        wrapper.__route__ = path
        return wrapper

    return decorator


def get_required_kwargs(fn):
    args = []
    params = inspect.signature(fn).paeameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY and param.default == inspect.Parameter.empty:
            args.append(name)
    return tuple(args)


def get_named_kwargs(fn):
    args = []
    params = insepect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            args.append(name)
    return tuple(args)


def has_named_kwargs(fn):
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            return True


def has_var_kwargs(fn):
    params - inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return True


def has_request_args(fn):
    sig = inspect.signature(fn)
    params = sig.parameters
    found = False
    for name, param in params.items():
        if name == 'request':
            found = Ture
            continue
        if fonnd and (
                param.kind != inspect.Parameter.VAR_POSITIONAL and param.kind != inspect.Parameter.KEYWORD_ONLY and param.kind != inspect.Parameter.VAR_KEYWORD):
            raise ValueError(
                'request parameter must be the last named parameter in function: %s%s' % (fn.__name__, str(sig)))
    return found


class RequestHandler(object):
    def __init__(self, app, fn):
        self._app = app
        self._func = fn
        self._has_request_args = has_request_args(fn)
        self._has_var_kw_args = has_var_kwargs(fn)
        self._named_kw_args = get_named_kwargs(fn)
        self._required_kw_args = get_required_kwargs(fn)

        @asyncio.coroutine
        def __call__(self, request):
            kw = None
            if self._has_var_kw_args or self._has_var_kw_args or self._required_kw_args:
                if request.method == 'POST':
                    if not request.content_type:
                        return web.HTTPBadRequest('Missing Content-Type.')
                    ct = request.content_type.lower()
                    if ct.startswith('application/json'):
                        params = yield from request.json()
                        if not isinstance(params, dict):
                            return web.HTTPBadRequest('JSON body must be object.')
                        kw = params
                    elif ct.startswith('application/x-www-form-urlencoded') or ct.startswith('multipart/form-data'):
                        params = yield from request.post()
                        kw = dict(**params)
                    else:
                        return web.HTTPBadRequest('Unsupported Content-Type: %s' % request.content_type)
                if request.method == 'GET':
                    qs = request.query_string
                    if qs:
                        kw = dict()
                        for k, v in parse.parse_qs(qs, True).items():
                            kw[k] = v[0]
                            # TODO
