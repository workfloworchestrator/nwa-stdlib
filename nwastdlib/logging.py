#  Copyright 2019 SURF.
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import logging.config
import os
from typing import Any, Dict, Optional

import structlog
from structlog.threadlocal import wrap_dict

pre_chain = [
    # Add the log level and a timestamp to the event_dict if the log entry
    # is not from structlog.
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
    structlog.stdlib.PositionalArgumentsFormatter(),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
]

LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
LOG_OUTPUT = os.getenv("LOG_OUTPUT", "colored")

# Must be called like so due to the gunicorn config do not rename
logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "plain": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(colors=False),
            "foreign_pre_chain": pre_chain,
        },
        "colored": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(colors=True),
            "foreign_pre_chain": pre_chain,
        },
        "json": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(sort_keys=True),
            "foreign_pre_chain": pre_chain,
        },
    },
    "handlers": {
        "default": {"class": "logging.StreamHandler", "formatter": LOG_OUTPUT},
        # These handlers are needed by gunicorn
        "error_console": {"class": "logging.StreamHandler", "formatter": LOG_OUTPUT},
        "console": {"class": "logging.StreamHandler", "formatter": LOG_OUTPUT},
        "gunicorn.error": {"class": "logging.StreamHandler", "formatter": LOG_OUTPUT},
    },
}


def initialise_logging(additional_loggers: Optional[Dict[str, Dict[str, Any]]] = None) -> None:
    """
    Initialise the StructLog logging setup.

    An example of the additional_loggers format:

    additional_logging = {
        "zeep.transports": {  # set to debug to see XML in loggging
            "level": os.environ.get("ZEEP_TRANSPORT_LOGLEVEL", "INFO").upper(),
            "propagate": True,
            "handlers": ["default"],
        },
        "ims.ims_client": {  # set to debug to see more messages from IMS client
            "level": os.environ.get("IMSCLIENT_LOGLEVEL", "INFO").upper(),
            "propagate": False,
            "handlers": ["default"],
        },
    }

    Args:
        additional_loggers: if you need additional loggers for specific log requirements of libraries you can add a
        dict with the additional config.

    """
    if additional_loggers is None:
        additional_loggers = {}

    logging.config.dictConfig(
        {
            "loggers": {
                "": {"handlers": ["default"], "level": f"{LOG_LEVEL}", "propagate": True},
                **additional_loggers,
            },
            **logconfig_dict,
        }
    )

    structlog.configure(
        processors=pre_chain + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],  # type: ignore
        context_class=wrap_dict(dict),  # type: ignore
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
