# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
# pylint: disable=R
import hashlib
import simplejson as json

from typing import Dict, List, Optional
from superset import app
from superset.utils import core as utils


# TODO: Type Metrics dictionary with TypedDict when it becomes a vanilla python type
# https://github.com/python/mypy/issues/5288

class QueryObject:
    """
    The query object's schema matches the interfaces of DB connectors like sqla
    and druid. The query objects are constructed on the client.
    """
    def __init__(
            self,
            granularity: str,
            groupby: List[str],
            metrics: List[Dict],
            filters: List[str],
            time_range: Optional[str] = None,
            time_shift: Optional[str] = None,
            is_timeseries: bool = False,
            row_limit: int = app.config.get('ROW_LIMIT'),
            limit: int = 0,
            timeseries_limit_metric: Optional[Dict] = None,
            order_desc: bool = True,
            extras: Optional[Dict] = None,
    ):
        self.granularity = granularity
        self.from_dttm, self.to_dttm = utils.get_since_until(time_range, time_shift)
        self.is_timeseries = is_timeseries
        self.groupby = groupby or []
        self.metrics = metrics or []
        self.filter = filters or []
        self.row_limit = row_limit
        self.timeseries_limit = int(limit)
        self.timeseries_limit_metric = timeseries_limit_metric
        self.order_desc = order_desc
        self.prequeries = []
        self.is_prequery = False
        self.extras = extras

    def to_dict(self):
        query_object_dict = {
            'granularity': self.granularity,
            'from_dttm': self.from_dttm,
            'to_dttm': self.to_dttm,
            'is_timeseries': self.is_timeseries,
            'groupby': self.groupby,
            'row_limit': self.row_limit,
            'filters': self.filter,
            'timeseries_limit': self.timeseries_limit,
            'timeseries_limit_metric': self.timeseries_limit_metric,
            'order_desc': self.order_desc,
            'prequeries': self.prequeries,
            'is_prequery': self.is_prequery,
        }
        query_object_dict.update(self.extras)
        return query_object_dict

    def cache_key(self, **extra):
        """
        The cache key is made out of the key/values in `query_obj`, plus any
        other key/values in `extra`
        We remove datetime bounds that are hard values, and replace them with
        the use-provided inputs to bounds, which may be time-relative (as in
        "5 days ago" or "now").
        """
        cache_dict = self.to_dict()
        cache_dict.update(extra)

        for k in ['from_dttm', 'to_dttm']:
            del cache_dict[k]

        cache_dict['time_range'] = self.time_range
        json_data = self.json_dumps(cache_dict, sort_keys=True)
        return hashlib.md5(json_data.encode('utf-8')).hexdigest()

    def json_dumps(self, obj, sort_keys=False):
        return json.dumps(
            obj,
            default=utils.json_int_dttm_ser,
            ignore_nan=True,
            sort_keys=sort_keys,
        )
