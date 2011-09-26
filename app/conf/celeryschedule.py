from datetime import timedelta

CELERYBEAT_SCHEDULE = {
    "reddit-validations": {
        "task": "reddit.tasks.process_validations",
        "schedule": timedelta(minutes=10),
    },
    "eveapi-update": {
        "task": "eve_api.tasks.account.queue_apikey_updates",
        "schedule": timedelta(minutes=10),
    },
    "alliance-update": {
        "task": "eve_api.tasks.alliance.import_alliance_details",
        "schedule": timedelta(hours=6),
    },
    "api-log-clear": {
        "task": "eve_proxy.tasks.clear_old_logs",
        "schedule": timedelta(days=1),
    },
    "blacklist-check": {
        "task": "hr.tasks.blacklist_check",
        "schedule": timedelta(days=7),
    },
    "reddit-update": {
        "task": "reddit.tasks.queue_account_updates",
        "schedule": timedelta(minutes=15),
    }
}

CELERY_ROUTES = {
    "sso.tasks.update_service_groups": {'queue': 'bulk'},
    "hr.tasks.blacklist_check": {'queue': 'bulk'},
    "eve_api.tasks.import_apikey_result": {'queue': 'fastresponse'},
    "sso.tasks.update_user_access":  {'queue': 'fastresponse'},
}
